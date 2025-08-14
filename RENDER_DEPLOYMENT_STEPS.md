# Quick Render Deployment Steps

## Easiest Method: Deploy from Feature Branch

1. **Go to Render Dashboard**: https://render.com/dashboard

2. **Click "New +" → "Blueprint"**

3. **Connect GitHub Repository**:
   - Repository: `oluwafemi02/predictor`
   - Branch: **`cursor/research-sportmonks-api-for-web-app-eb28`** ← IMPORTANT!
   - The render.yaml file is on this branch

4. **Name Your Blueprint**: "Football Prediction SportMonks"

5. **Click "Apply"**

6. **Wait for Services to Create** (5-10 minutes)

7. **Add SportMonks API Key**:
   - Go to `football-prediction-backend` service
   - Click "Environment" tab
   - Add: `SPORTMONKS_API_KEY` = `cCo0Sn0Fj6BnSmdigHu0oveKznsuZMZzXYe0jIaDDmo8ZymwBP7XjFZCYJPh`
   - Click "Save Changes"

8. **Initialize Database**:
   - Go to backend service → "Shell" tab
   - Run: `python deploy_sportmonks.py`

9. **Access Your App**:
   - Frontend will be at: `https://football-prediction-frontend-[random].onrender.com/sportmonks`

## If Blueprint Doesn't Show render.yaml

Make sure you:
1. Selected the correct branch: `cursor/research-sportmonks-api-for-web-app-eb28`
2. The render.yaml is in the root of the repository
3. Try refreshing the page after selecting the branch

## Alternative: Merge to Main First

1. Go to https://github.com/oluwafemi02/predictor/compare
2. Create PR from `cursor/research-sportmonks-api-for-web-app-eb28` to `main`
3. Merge the PR
4. Then use Blueprint with `main` branch