package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"github.com/devmind-pipeline/pipeline/internal/config"
	"github.com/devmind-pipeline/pipeline/internal/server"
	"github.com/devmind-pipeline/pipeline/pkg/logging"
	"github.com/devmind-pipeline/pipeline/pkg/metrics"
	"github.com/devmind-pipeline/pipeline/pkg/tracing"
)

var (
	cfgFile string
	logger  *logrus.Logger
)

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

var rootCmd = &cobra.Command{
	Use:   "pipeline-engine",
	Short: "DevMind Pipeline Engine - High-performance pipeline execution with AI integration",
	Long: `DevMind Pipeline Engine is a high-performance, AI-enhanced pipeline execution engine
that integrates with Tekton and ArgoCD for cloud-native CI/CD workflows.

Features:
- AI-powered build optimization
- Intelligent failure prediction
- Smart test selection
- Real-time monitoring and metrics
- Tekton and ArgoCD integration
- Kubernetes-native architecture`,
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		// Initialize configuration
		if err := initConfig(); err != nil {
			return fmt.Errorf("failed to initialize config: %w", err)
		}

		// Initialize logging
		logger = logging.NewLogger()
		
		// Initialize metrics
		if err := metrics.Initialize(); err != nil {
			return fmt.Errorf("failed to initialize metrics: %w", err)
		}

		// Initialize tracing
		if err := tracing.Initialize(); err != nil {
			logger.WithError(err).Warn("Failed to initialize tracing")
		}

		return nil
	},
	RunE: func(cmd *cobra.Command, args []string) error {
		return runServer()
	},
}

var serverCmd = &cobra.Command{
	Use:   "server",
	Short: "Start the pipeline engine server",
	Long:  "Start the pipeline engine server with gRPC and HTTP APIs",
	RunE: func(cmd *cobra.Command, args []string) error {
		return runServer()
	},
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print version information",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("DevMind Pipeline Engine\n")
		fmt.Printf("Version: %s\n", config.Version)
		fmt.Printf("Build Date: %s\n", config.BuildDate)
		fmt.Printf("Git Commit: %s\n", config.GitCommit)
	},
}

func init() {
	cobra.OnInitialize(initConfig)

	// Global flags
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.pipeline-engine.yaml)")
	rootCmd.PersistentFlags().String("log-level", "info", "log level (debug, info, warn, error)")
	rootCmd.PersistentFlags().String("log-format", "json", "log format (json, text)")
	rootCmd.PersistentFlags().Bool("metrics-enabled", true, "enable prometheus metrics")
	rootCmd.PersistentFlags().Bool("tracing-enabled", true, "enable distributed tracing")

	// Server flags
	serverCmd.Flags().String("grpc-port", "8080", "gRPC server port")
	serverCmd.Flags().String("http-port", "8081", "HTTP server port")
	serverCmd.Flags().String("metrics-port", "9090", "metrics server port")
	serverCmd.Flags().Int("max-concurrent-pipelines", 100, "maximum concurrent pipelines")
	serverCmd.Flags().Duration("shutdown-timeout", 30*time.Second, "graceful shutdown timeout")

	// Bind flags to viper
	viper.BindPFlags(rootCmd.PersistentFlags())
	viper.BindPFlags(serverCmd.Flags())

	// Add subcommands
	rootCmd.AddCommand(serverCmd)
	rootCmd.AddCommand(versionCmd)
}

func initConfig() error {
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		home, err := os.UserHomeDir()
		if err != nil {
			return err
		}

		viper.AddConfigPath(home)
		viper.AddConfigPath(".")
		viper.AddConfigPath("/etc/pipeline-engine/")
		viper.SetConfigType("yaml")
		viper.SetConfigName(".pipeline-engine")
	}

	// Environment variables
	viper.SetEnvPrefix("PIPELINE")
	viper.AutomaticEnv()

	// Default values
	setDefaults()

	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return fmt.Errorf("failed to read config file: %w", err)
		}
	}

	return nil
}

func setDefaults() {
	// Server defaults
	viper.SetDefault("server.grpc_port", "8080")
	viper.SetDefault("server.http_port", "8081")
	viper.SetDefault("server.metrics_port", "9090")
	viper.SetDefault("server.max_concurrent_pipelines", 100)
	viper.SetDefault("server.shutdown_timeout", "30s")

	// Logging defaults
	viper.SetDefault("logging.level", "info")
	viper.SetDefault("logging.format", "json")

	// Tekton defaults
	viper.SetDefault("tekton.namespace", "tekton-pipelines")
	viper.SetDefault("tekton.timeout", "30m")
	viper.SetDefault("tekton.retry_count", 3)

	// ArgoCD defaults
	viper.SetDefault("argocd.server", "argocd-server:443")
	viper.SetDefault("argocd.timeout", "5m")
	viper.SetDefault("argocd.insecure", false)

	// AI service defaults
	viper.SetDefault("ai_service.url", "http://ml-service:8000")
	viper.SetDefault("ai_service.timeout", "30s")
	viper.SetDefault("ai_service.enabled", true)

	// Database defaults
	viper.SetDefault("database.type", "postgresql")
	viper.SetDefault("database.host", "localhost")
	viper.SetDefault("database.port", 5432)
	viper.SetDefault("database.name", "pipeline_engine")
	viper.SetDefault("database.ssl_mode", "disable")

	// Redis defaults
	viper.SetDefault("redis.host", "localhost")
	viper.SetDefault("redis.port", 6379)
	viper.SetDefault("redis.db", 0)

	// Metrics defaults
	viper.SetDefault("metrics.enabled", true)
	viper.SetDefault("metrics.path", "/metrics")
	viper.SetDefault("metrics.namespace", "devmind_pipeline")

	// Tracing defaults
	viper.SetDefault("tracing.enabled", true)
	viper.SetDefault("tracing.jaeger_endpoint", "http://jaeger:14268/api/traces")
	viper.SetDefault("tracing.service_name", "pipeline-engine")
}

func runServer() error {
	logger.Info("Starting DevMind Pipeline Engine")

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	logger.WithFields(logrus.Fields{
		"grpc_port":               cfg.Server.GRPCPort,
		"http_port":               cfg.Server.HTTPPort,
		"metrics_port":            cfg.Server.MetricsPort,
		"max_concurrent_pipelines": cfg.Server.MaxConcurrentPipelines,
	}).Info("Server configuration loaded")

	// Create server
	srv, err := server.New(cfg, logger)
	if err != nil {
		return fmt.Errorf("failed to create server: %w", err)
	}

	// Create context for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start server
	errCh := make(chan error, 1)
	go func() {
		if err := srv.Start(ctx); err != nil {
			errCh <- fmt.Errorf("server failed: %w", err)
		}
	}()

	// Wait for interrupt signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	select {
	case err := <-errCh:
		logger.WithError(err).Error("Server error")
		return err
	case sig := <-sigCh:
		logger.WithField("signal", sig).Info("Received shutdown signal")
	}

	// Graceful shutdown
	logger.Info("Shutting down server...")
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), cfg.Server.ShutdownTimeout)
	defer shutdownCancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		logger.WithError(err).Error("Failed to shutdown server gracefully")
		return err
	}

	logger.Info("Server shutdown complete")
	return nil
}