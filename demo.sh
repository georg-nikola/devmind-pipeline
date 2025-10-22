#!/bin/bash
# DevMind Pipeline - Interactive Demo Script
# The API is running on http://localhost:8001

API_URL="http://localhost:8001"
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}========================================${NC}"
echo -e "${BOLD}${BLUE}  DevMind Pipeline - Interactive Demo  ${NC}"
echo -e "${BOLD}${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}API running at: ${API_URL}${NC}"
echo ""

# Function to pretty print JSON
pretty_json() {
    python3 -m json.tool
}

# Function to run demo with description
run_demo() {
    local title=$1
    local description=$2
    local command=$3

    echo -e "${YELLOW}${BOLD}▶ ${title}${NC}"
    echo -e "  ${description}"
    echo ""
    eval "$command" | pretty_json
    echo ""
    echo "---"
    echo ""
}

# Main menu
echo "Choose a demo to run:"
echo ""
echo "1. Health Check - Verify service is running"
echo "2. Build Optimization - Get AI-powered build recommendations"
echo "3. Failure Prediction - Predict pipeline failure probability"
echo "4. Test Intelligence - Smart test selection"
echo "5. Cache Strategy - Get intelligent caching recommendations"
echo "6. Flaky Test Detection - Find unreliable tests"
echo "7. Build Statistics - View build performance metrics"
echo "8. Anomaly Detection - Detect unusual pipeline behavior"
echo "9. Run All Demos - Execute all examples"
echo "0. Exit"
echo ""
read -p "Enter your choice (0-9): " choice

case $choice in
    1)
        run_demo "Health Check" \
            "Check if ML models are loaded and service is healthy" \
            "curl -s ${API_URL}/health"
        ;;
    2)
        run_demo "Build Optimization" \
            "Get AI recommendations to optimize build time" \
            "curl -s -X POST ${API_URL}/api/v1/build-optimizer/optimize \
                -H 'Content-Type: application/json' \
                -d '{
                    \"project_name\": \"my-awesome-app\",
                    \"dependency_graph\": {\"frontend\": [\"api\"], \"api\": [\"database\"], \"database\": []},
                    \"historical_build_times\": [180, 195, 175, 190, 185],
                    \"resource_constraints\": {\"cpu\": 4, \"memory\": \"8GB\"}
                }'"
        ;;
    3)
        run_demo "Failure Prediction" \
            "Predict if the next pipeline run will fail" \
            "curl -s -X POST ${API_URL}/api/v1/failure-predictor/predict \
                -H 'Content-Type: application/json' \
                -d '{
                    \"pipeline_id\": \"prod-deployment-pipeline\",
                    \"commit_hash\": \"a1b2c3d4e5f6\",
                    \"code_changes\": {
                        \"files_changed\": 25,
                        \"lines_added\": 450,
                        \"lines_deleted\": 180
                    },
                    \"historical_metrics\": {
                        \"avg_build_time\": 200,
                        \"test_count\": 380,
                        \"coverage\": 85.0
                    }
                }'"
        ;;
    4)
        run_demo "Test Intelligence" \
            "Get smart test selection based on code changes" \
            "curl -s -X POST ${API_URL}/api/v1/test-intelligence/select \
                -H 'Content-Type: application/json' \
                -d '{
                    \"project_name\": \"my-app\",
                    \"commit_hash\": \"abc123\",
                    \"changed_files\": [
                        \"src/auth/login.py\",
                        \"src/api/users.py\",
                        \"src/utils/validation.py\"
                    ],
                    \"all_tests\": [
                        \"tests/test_auth.py\",
                        \"tests/test_api.py\",
                        \"tests/test_database.py\",
                        \"tests/test_integration.py\",
                        \"tests/test_utils.py\"
                    ]
                }'"
        ;;
    5)
        run_demo "Cache Strategy" \
            "Get intelligent caching recommendations" \
            "curl -s ${API_URL}/api/v1/build-optimizer/cache-strategy/my-awesome-app"
        ;;
    6)
        run_demo "Flaky Test Detection" \
            "Detect tests that fail intermittently" \
            "curl -s '${API_URL}/api/v1/test-intelligence/flaky-tests/my-app?days=30'"
        ;;
    7)
        run_demo "Build Statistics" \
            "View historical build performance" \
            "curl -s '${API_URL}/api/v1/build-optimizer/statistics/my-awesome-app?days=30'"
        ;;
    8)
        run_demo "Anomaly Detection" \
            "Detect unusual patterns in pipeline metrics" \
            "curl -s '${API_URL}/api/v1/failure-predictor/anomalies/prod-pipeline?window_hours=24'"
        ;;
    9)
        echo -e "${BOLD}${GREEN}Running all demos...${NC}"
        echo ""

        run_demo "1. Health Check" \
            "Verifying service status" \
            "curl -s ${API_URL}/health"

        run_demo "2. Build Optimization" \
            "Getting build recommendations" \
            "curl -s -X POST ${API_URL}/api/v1/build-optimizer/optimize \
                -H 'Content-Type: application/json' \
                -d '{\"project_name\": \"demo-project\", \"historical_build_times\": [150, 160, 155]}'"

        run_demo "3. Failure Prediction" \
            "Predicting pipeline failure" \
            "curl -s -X POST ${API_URL}/api/v1/failure-predictor/predict \
                -H 'Content-Type: application/json' \
                -d '{\"pipeline_id\": \"demo-pipeline\", \"code_changes\": {\"files_changed\": 10}}'"

        run_demo "4. Test Intelligence" \
            "Smart test selection" \
            "curl -s -X POST ${API_URL}/api/v1/test-intelligence/select \
                -H 'Content-Type: application/json' \
                -d '{\"project_name\": \"demo\", \"commit_hash\": \"abc\", \"changed_files\": [\"src/main.py\"]}'"

        run_demo "5. Cache Strategy" \
            "Caching recommendations" \
            "curl -s ${API_URL}/api/v1/build-optimizer/cache-strategy/demo-project"

        run_demo "6. Flaky Tests" \
            "Detecting unreliable tests" \
            "curl -s '${API_URL}/api/v1/test-intelligence/flaky-tests/demo-project'"

        echo -e "${GREEN}${BOLD}All demos completed!${NC}"
        ;;
    0)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}${BOLD}Additional Resources:${NC}"
echo "  • API Documentation: ${API_URL}/docs"
echo "  • ReDoc: ${API_URL}/redoc"
echo "  • Metrics: ${API_URL}/metrics"
echo "  • Model Status: ${API_URL}/models/status"
echo ""
echo -e "${GREEN}Run this script again to try other demos!${NC}"
