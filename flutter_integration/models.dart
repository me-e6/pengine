/// DataNarrative Flutter Models
/// ============================
/// Data models for API responses

// Query Analysis
class QueryAnalysis {
  final String intent;
  final double intentConfidence;
  final List<String> topics;
  final List<String> locations;
  final List<String> timeReferences;
  final String? domainHint;
  final bool requiresHistorical;
  final String preferredOutput;

  QueryAnalysis({
    required this.intent,
    required this.intentConfidence,
    required this.topics,
    required this.locations,
    required this.timeReferences,
    this.domainHint,
    required this.requiresHistorical,
    required this.preferredOutput,
  });

  factory QueryAnalysis.fromJson(Map<String, dynamic> json) {
    return QueryAnalysis(
      intent: json['intent'] ?? '',
      intentConfidence: (json['intent_confidence'] ?? 0).toDouble(),
      topics: List<String>.from(json['topics'] ?? []),
      locations: List<String>.from(json['locations'] ?? []),
      timeReferences: List<String>.from(json['time_references'] ?? []),
      domainHint: json['domain_hint'],
      requiresHistorical: json['requires_historical'] ?? false,
      preferredOutput: json['preferred_output'] ?? 'data',
    );
  }
}

// Insight
class Insight {
  final String type;
  final String summary;
  final double confidence;
  final String? metricName;
  final double? currentValue;
  final double? changePercentage;
  final String? direction;
  final String? sentiment;

  Insight({
    required this.type,
    required this.summary,
    required this.confidence,
    this.metricName,
    this.currentValue,
    this.changePercentage,
    this.direction,
    this.sentiment,
  });

  factory Insight.fromJson(Map<String, dynamic> json) {
    return Insight(
      type: json['type'] ?? '',
      summary: json['summary'] ?? '',
      confidence: (json['confidence'] ?? 0).toDouble(),
      metricName: json['metric_name'],
      currentValue: json['current_value']?.toDouble(),
      changePercentage: json['change_percentage']?.toDouble(),
      direction: json['direction'],
      sentiment: json['sentiment'],
    );
  }
}

// Narrative Frame
class NarrativeFrame {
  final String type;
  final String headline;
  final String bodyText;
  final String? keyMetric;
  final String? keyMetricLabel;

  NarrativeFrame({
    required this.type,
    required this.headline,
    required this.bodyText,
    this.keyMetric,
    this.keyMetricLabel,
  });

  factory NarrativeFrame.fromJson(Map<String, dynamic> json) {
    return NarrativeFrame(
      type: json['type'] ?? '',
      headline: json['headline'] ?? '',
      bodyText: json['body_text'] ?? '',
      keyMetric: json['key_metric'],
      keyMetricLabel: json['key_metric_label'],
    );
  }
}

// Query Response
class QueryResponse {
  final bool success;
  final String query;
  final QueryAnalysis analysis;
  final String outputMode;
  final String templateUsed;
  final List<Insight> insights;
  final Insight? primaryInsight;
  final String? narrativeTitle;
  final String? narrativeSubtitle;
  final List<NarrativeFrame>? narrativeFrames;
  final String? imageUrl;
  final String? imageId;
  final List<String> sourcesUsed;
  final double confidence;
  final double processingTimeMs;

  QueryResponse({
    required this.success,
    required this.query,
    required this.analysis,
    required this.outputMode,
    required this.templateUsed,
    required this.insights,
    this.primaryInsight,
    this.narrativeTitle,
    this.narrativeSubtitle,
    this.narrativeFrames,
    this.imageUrl,
    this.imageId,
    required this.sourcesUsed,
    required this.confidence,
    required this.processingTimeMs,
  });

  factory QueryResponse.fromJson(Map<String, dynamic> json) {
    return QueryResponse(
      success: json['success'] ?? false,
      query: json['query'] ?? '',
      analysis: QueryAnalysis.fromJson(json['analysis'] ?? {}),
      outputMode: json['output_mode'] ?? 'data',
      templateUsed: json['template_used'] ?? '',
      insights: (json['insights'] as List?)
          ?.map((e) => Insight.fromJson(e))
          .toList() ?? [],
      primaryInsight: json['primary_insight'] != null
          ? Insight.fromJson(json['primary_insight'])
          : null,
      narrativeTitle: json['narrative_title'],
      narrativeSubtitle: json['narrative_subtitle'],
      narrativeFrames: (json['narrative_frames'] as List?)
          ?.map((e) => NarrativeFrame.fromJson(e))
          .toList(),
      imageUrl: json['image_url'],
      imageId: json['image_id'],
      sourcesUsed: List<String>.from(json['sources_used'] ?? []),
      confidence: (json['confidence'] ?? 0).toDouble(),
      processingTimeMs: (json['processing_time_ms'] ?? 0).toDouble(),
    );
  }
}

// Render Response
class RenderResponse {
  final bool success;
  final String infogramId;
  final String imageUrl;
  final String templateUsed;
  final int width;
  final int height;
  final double renderTimeMs;
  final List<String>? imageUrls;
  final int imageCount;

  RenderResponse({
    required this.success,
    required this.infogramId,
    required this.imageUrl,
    required this.templateUsed,
    required this.width,
    required this.height,
    required this.renderTimeMs,
    this.imageUrls,
    required this.imageCount,
  });

  factory RenderResponse.fromJson(Map<String, dynamic> json) {
    return RenderResponse(
      success: json['success'] ?? false,
      infogramId: json['infogram_id'] ?? '',
      imageUrl: json['image_url'] ?? '',
      templateUsed: json['template_used'] ?? '',
      width: json['width'] ?? 1080,
      height: json['height'] ?? 1350,
      renderTimeMs: (json['render_time_ms'] ?? 0).toDouble(),
      imageUrls: json['image_urls'] != null
          ? List<String>.from(json['image_urls'])
          : null,
      imageCount: json['image_count'] ?? 1,
    );
  }
}

// Template Info
class TemplateInfo {
  final String id;
  final String name;
  final String description;
  final List<String> bestFor;

  TemplateInfo({
    required this.id,
    required this.name,
    required this.description,
    required this.bestFor,
  });

  factory TemplateInfo.fromJson(Map<String, dynamic> json) {
    return TemplateInfo(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      bestFor: List<String>.from(json['best_for'] ?? []),
    );
  }
}

// Ingest Result
class IngestResult {
  final bool success;
  final String fileId;
  final String filename;
  final String sourceName;
  final int tablesFound;
  final int chunksCreated;
  final int chunksStored;
  final List<String> domainsDetected;
  final bool hasHistoricalData;
  final List<int>? timeRange;
  final List<String> regionsDetected;
  final double processingTimeSeconds;
  final List<String> errors;
  final List<String> warnings;

  IngestResult({
    required this.success,
    required this.fileId,
    required this.filename,
    required this.sourceName,
    required this.tablesFound,
    required this.chunksCreated,
    required this.chunksStored,
    required this.domainsDetected,
    required this.hasHistoricalData,
    this.timeRange,
    required this.regionsDetected,
    required this.processingTimeSeconds,
    required this.errors,
    required this.warnings,
  });

  factory IngestResult.fromJson(Map<String, dynamic> json) {
    return IngestResult(
      success: json['success'] ?? false,
      fileId: json['file_id'] ?? '',
      filename: json['filename'] ?? '',
      sourceName: json['source_name'] ?? '',
      tablesFound: json['tables_found'] ?? 0,
      chunksCreated: json['chunks_created'] ?? 0,
      chunksStored: json['chunks_stored'] ?? 0,
      domainsDetected: List<String>.from(json['domains_detected'] ?? []),
      hasHistoricalData: json['has_historical_data'] ?? false,
      timeRange: json['time_range'] != null
          ? List<int>.from(json['time_range'])
          : null,
      regionsDetected: List<String>.from(json['regions_detected'] ?? []),
      processingTimeSeconds: (json['processing_time_seconds'] ?? 0).toDouble(),
      errors: List<String>.from(json['errors'] ?? []),
      warnings: List<String>.from(json['warnings'] ?? []),
    );
  }
}
