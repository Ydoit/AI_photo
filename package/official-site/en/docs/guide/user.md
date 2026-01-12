# TrailSnap User Guide

Welcome to TrailSnap! TrailSnap is an intelligent AI photo album application that not only helps you manage photos but also automatically identifies photo content, organizes itinerary tickets, and even generates travel VLOGs with one click using AI technology.

This document will detail TrailSnap's main features, usage methods, and operation flows.

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Album Management](#2-album-management)
3. [Smart Features](#3-smart-features)
4. [Itinerary & Tickets](#4-itinerary-tickets)
5. [System Settings](#5-system-settings)

## 1. Quick Start

### Login/Register
When accessing the system for the first time, please log in using the account distributed by the administrator or register a new account as prompted.

### Dashboard Overview
After logging in, you will see the system dashboard, which includes:
- **Data Overview**: Displays statistics such as total photos, albums, and footprint points.
- **Recent Memories**: Displays recently uploaded photos or activities in a timeline format.
- **Feature Shortcuts**: Quick access to albums, tickets, map footprints, and other features.

### Add External Library

1. Click "Settings -> External Libraries" in the navigation bar.
2. Enter the address of the external library, e.g., `/app/photos` (pay attention to the docker mount path).
3. Click Confirm, and the system will automatically scan all photos in that directory (task progress can be viewed in "Settings -> Task Management").

## 2. Album Management

### Create Album
1. Click "Albums" or the "New Album" button in the navigation bar.
2. Enter the album name, description, and select an album cover (optional).
3. Click Confirm to create.

### Upload Photos
1. Enter any album or click the global "Upload" button.
2. Supports drag-and-drop upload or click to select files.
3. Supports batch upload; the system will automatically read the photo's EXIF information (shooting time, location, etc.).

### Photo Browsing
- **Timeline View**: Arranges photos in chronological order of shooting, suitable for reviewing journeys.
- **Map View**: Displays photo shooting locations on the map, lighting up your footprints.
- **Detail View**: Click on a photo to view the large image and detailed metadata (ISO, shutter, device model, etc.).

## 3. Smart Features

TrailSnap has built-in powerful AI services to provide you with the following intelligent experiences:

### Face Recognition & Clustering
- The system automatically analyzes uploaded photos and identifies faces.
- Automatically groups photos of the same person into "People Albums".
- You can name the identified people, and the system will automatically associate all photos of that person.

### Smart Search (OCR & Content Recognition)
- **Text Search**: Supports searching for text in photos (such as street signs, menus, text on tickets).
- **Semantic Search**: Search by directly describing the photo content, such as "sunset by the sea", "friends skiing", AI can understand your natural language description.

### AI Retouching & VLOG Generation
- **One-click Retouching**: Uses AI algorithms to automatically adjust photo color and exposure to improve image quality.
- **Generate VLOG**: Select a journey or an album, and AI will automatically pick highlights, add music, and generate a short video.

## 4. Itinerary & Tickets

This is a featured function of TrailSnap designed for travelers.

### Ticket Management
- **Automatic Recognition**: Upload photos of train tickets, flight tickets, scenic spot tickets, or concert tickets.
- **OCR Extraction**: The system automatically extracts key information from tickets (departure, destination, time, train/flight number, seat number, etc.).
- **Manual Entry**: If recognition is incorrect, manual modification or supplementation of information is supported.

### Itinerary Timeline
- The system automatically generates a complete "Travel Timeline" based on your ticket times and photo times.
- You can clearly see the complete trajectory from departure to return.

## 5. System Settings

On the settings page, you can configure the following:

- **Personal Information**: Modify avatar, nickname, password.
- **Theme Settings**: Switch between light/dark modes, or follow the system automatically.
- **Storage Settings**: View storage space usage.
- **Task Management**: View background task progress (such as ongoing AI recognition tasks, thumbnail generation tasks).

If you have any usage questions, please contact the system administrator or consult the [Developer Documentation](/en/docs/dev/guide).
