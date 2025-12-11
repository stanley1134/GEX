# How to Deploy GEX App to Render.com

## 1. Prepare Your Code
Your project is already configured for Render with these files:
- **`Procfile`**: Tells Render how to run the app (`gunicorn webapp.app:app`).
- **`requirements.txt`**: Lists dependencies (including `gunicorn`).
- **`runtime.txt`**: Specifies Python version (`3.12.15`).

## 2. Push to GitHub
If you haven't already, push your code to a GitHub repository:
1. Create a new repo on GitHub.
2. Run these commands in your project folder:
   ```bash
   git init
   git add .
   git commit -m "Ready for Render"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

## 3. Create Web Service on Render
1. Go to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub account and select your repository.
4. Configure the service:
   - **Name**: `gex-app` (or whatever you like)
   - **Region**: Closest to you (e.g., Ohio, Oregon)
   - **Branch**: `main`
   - **Root Directory**: `.` (leave empty)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn webapp.app:app`

## 4. Environment Variables
In the Render dashboard for your service, go to **Environment** tab and add:
- Key: `TRADIER_API_KEY`
- Value: `<your-tradier-api-key>` (Copy from your local .env)

- Key: `GEMINI_API_KEY`
- Value: `<your-gemini-api-key>` (If you plan to fix/use AI later)

## 5. Deploy
- Click **Create Web Service**.
- Render will start building. Watch the logs.
- Once unrelated, successful, you'll see a green "Live" badge and your URL (e.g., `https://gex-app.onrender.com`).

## Troubleshooting
- **Build Fails?** Check logs. If `requirements.txt` has issues, Render will show them.
- **App Crashes?** Check "Logs" tab. Common issue is missing API keys.
