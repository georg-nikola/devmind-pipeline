import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  ChartBarIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  TrendingUpIcon,
  TrendingDownIcon,
} from '@heroicons/react/24/outline';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';

import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { aiService } from '../services/aiService';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface AIInsightsData {
  buildOptimization: {
    totalOptimized: number;
    averageTimeSaved: number;
    optimizationPotential: number;
    recommendations: Array<{
      id: string;
      type: string;
      description: string;
      impact: 'high' | 'medium' | 'low';
      estimatedSavings: string;
    }>;
  };
  failurePrediction: {
    accuracy: number;
    totalPredictions: number;
    preventedFailures: number;
    riskDistribution: {
      low: number;
      medium: number;
      high: number;
      critical: number;
    };
  };
  testIntelligence: {
    testsOptimized: number;
    timeReduction: number;
    coverageMaintained: number;
    flakyTestsDetected: number;
  };
  modelPerformance: {
    buildOptimizer: {
      accuracy: number;
      lastTrained: string;
      status: 'healthy' | 'warning' | 'error';
    };
    failurePredictor: {
      precision: number;
      recall: number;
      lastTrained: string;
      status: 'healthy' | 'warning' | 'error';
    };
    testIntelligence: {
      efficiency: number;
      lastTrained: string;
      status: 'healthy' | 'warning' | 'error';
    };
  };
}

export const AIInsights: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');

  const { data: insights, isLoading, error } = useQuery<AIInsightsData>(
    ['ai-insights', selectedTimeRange],
    () => aiService.getInsights(selectedTimeRange),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Failed to load AI insights
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Please try again later or check your connection.
          </p>
        </div>
      </div>
    );
  }

  const buildOptimizationChartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Time Saved (minutes)',
        data: [120, 180, 250, 320, 280, 350],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const failureRiskChartData = {
    labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk'],
    datasets: [
      {
        data: [
          insights?.failurePrediction.riskDistribution.low || 0,
          insights?.failurePrediction.riskDistribution.medium || 0,
          insights?.failurePrediction.riskDistribution.high || 0,
          insights?.failurePrediction.riskDistribution.critical || 0,
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(251, 191, 36, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderWidth: 0,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  const getRiskBadgeColor = (risk: string) => {
    switch (risk) {
      case 'high':
        return 'red';
      case 'medium':
        return 'yellow';
      case 'low':
        return 'green';
      default:
        return 'gray';
    }
  };

  const getModelStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'error':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            AI Insights
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Intelligent analysis and recommendations for your DevOps workflows
          </p>
        </div>
        <div className="flex space-x-2">
          {['24h', '7d', '30d'].map((range) => (
            <Button
              key={range}
              variant={selectedTimeRange === range ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setSelectedTimeRange(range)}
            >
              {range}
            </Button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUpIcon className="h-8 w-8 text-green-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Build Time Saved
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {insights?.buildOptimization.averageTimeSaved || 0}min
              </p>
              <p className="text-xs text-green-600 dark:text-green-400">
                +12% from last week
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="h-8 w-8 text-orange-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Failures Prevented
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {insights?.failurePrediction.preventedFailures || 0}
              </p>
              <p className="text-xs text-orange-600 dark:text-orange-400">
                {insights?.failurePrediction.accuracy || 0}% accuracy
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Tests Optimized
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {insights?.testIntelligence.testsOptimized || 0}
              </p>
              <p className="text-xs text-blue-600 dark:text-blue-400">
                {insights?.testIntelligence.timeReduction || 0}% time reduction
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CpuChipIcon className="h-8 w-8 text-purple-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                AI Predictions
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {insights?.failurePrediction.totalPredictions || 0}
              </p>
              <p className="text-xs text-purple-600 dark:text-purple-400">
                Last 24 hours
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
              Build Optimization Trends
            </h3>
            <div className="h-64">
              <Line data={buildOptimizationChartData} options={chartOptions} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
              Failure Risk Distribution
            </h3>
            <div className="h-64">
              <Doughnut
                data={failureRiskChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom',
                    },
                  },
                }}
              />
            </div>
          </div>
        </Card>
      </div>

      {/* AI Recommendations */}
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              AI Recommendations
            </h3>
            <LightBulbIcon className="h-5 w-5 text-yellow-500" />
          </div>
          <div className="space-y-4">
            {insights?.buildOptimization.recommendations.map((recommendation) => (
              <div
                key={recommendation.id}
                className="flex items-start space-x-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div className="flex-shrink-0">
                  <Badge color={getRiskBadgeColor(recommendation.impact)}>
                    {recommendation.impact}
                  </Badge>
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {recommendation.type}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {recommendation.description}
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-2">
                    Estimated savings: {recommendation.estimatedSavings}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Model Performance */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
            ML Model Performance
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                Build Optimizer
              </h4>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {insights?.modelPerformance.buildOptimizer.accuracy || 0}%
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Accuracy
                </div>
                <div
                  className={`text-xs ${getModelStatusColor(
                    insights?.modelPerformance.buildOptimizer.status || 'error'
                  )}`}
                >
                  {insights?.modelPerformance.buildOptimizer.status}
                </div>
              </div>
            </div>

            <div className="text-center">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                Failure Predictor
              </h4>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {insights?.modelPerformance.failurePredictor.precision || 0}%
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Precision
                </div>
                <div
                  className={`text-xs ${getModelStatusColor(
                    insights?.modelPerformance.failurePredictor.status || 'error'
                  )}`}
                >
                  {insights?.modelPerformance.failurePredictor.status}
                </div>
              </div>
            </div>

            <div className="text-center">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                Test Intelligence
              </h4>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {insights?.modelPerformance.testIntelligence.efficiency || 0}%
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Efficiency
                </div>
                <div
                  className={`text-xs ${getModelStatusColor(
                    insights?.modelPerformance.testIntelligence.status || 'error'
                  )}`}
                >
                  {insights?.modelPerformance.testIntelligence.status}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};