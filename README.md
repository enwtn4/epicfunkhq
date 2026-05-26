# Epic Funk HQ - Deployment Guide

## What you have
A complete band management web app with:
- Member login and registration
- Song library (admin can add/edit/delete)
- Gig calendar with RSVP (Yes / No / Maybe)
- Announcements with pin support
- Member directory with admin controls
- Mobile-friendly dark gold interface

## Files in this folder
- app.py - main application
- requirements.txt - Python dependencies
- Procfile - tells Railway how to run it
- templates/ - all the HTML pages

---

## Deploy to Railway (free, 15 minutes)

### Step 1 - Create a GitHub repo
1. Go to github.com and create a new repository called epicfunkhq
2. Upload all these files to the repo (drag and drop works)

### Step 2 - Deploy on Railway
1. Go to railway.app
2. Click "Start a New Project"
3. Choose "Deploy from GitHub repo"
4. Select your epicfunkhq repo
5. Railway detects Python automatically and deploys it

### Step 3 - Set environment variables
In Railway, go to your project settings and add:
- SECRET_KEY = any long random string (example: epicfunk2026xjacksonms)

That is the only variable required. Railway handles everything else.

### Step 4 - Get your URL
Railway gives you a free URL like epicfunkhq-production.up.railway.app
Share that URL with your band members.

---

## How it works for members
1. Band member goes to your Railway URL
2. Clicks Register and creates an account with name, instrument, email, password
3. YOU were the first to register so you are automatically the admin
4. Members can RSVP to gigs, view announcements, and see the song library
5. Only admins can add songs, gigs, and announcements

---

## Running locally to test first
1. Install Python if not already installed
2. Open terminal in this folder
3. Run: pip install -r requirements.txt
4. Run: python app.py
5. Open browser to http://localhost:5000

---

## Adding features later
Just bring the files back to Claude chat and say what you want to add.
All the code is plain Python and HTML, nothing complicated.
