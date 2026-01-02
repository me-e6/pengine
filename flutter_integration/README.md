# Flutter Integration Guide

## Overview

This guide shows how to integrate DataNarrative with your Flutter app.

## Quick Setup

### 1. Add Dependencies

```yaml
# pubspec.yaml
dependencies:
  http: ^1.1.0
  dio: ^5.3.0  # Alternative with more features
  cached_network_image: ^3.3.0
  provider: ^6.0.0  # For state management
```

### 2. Create API Service

See `datanarrative_service.dart` for complete implementation.

### 3. Basic Usage

```dart
final service = DataNarrativeService();

// Process a query
final result = await service.processQuery(
  'How has literacy changed in Telangana?',
  domainHint: 'education',
);

// Display the infographic
Image.network(result.imageUrl);
```

## Files Included

- `datanarrative_service.dart` - Main API service
- `models.dart` - Data models
- `widgets/` - Ready-to-use widgets
- `example_screens/` - Example implementations
