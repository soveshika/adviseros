#!/bin/bash

# Start PostgreSQL
brew services start postgresql@16

# Start Backend
cd /Users/mrsonusonu/Desktop/adviseros
source .venv311/bin/activate
uvicorn app.main:app --reload &

# Start Frontend
cd /Users/mrsonusonu/Desktop/adviseros-frontend
npm start