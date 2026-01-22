#!/bin/bash

# Start FastAPI in the background
python fast_app_ai.py &

# Start Streamlit in the foreground
# We bind it to 0.0.0.0 so it's accessible outside the container
streamlit run frontend_app.py --server.port 8501 --server.address 0.0.0.0