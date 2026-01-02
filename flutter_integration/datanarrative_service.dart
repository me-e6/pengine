/// DataNarrative API Service
/// =========================
/// Complete Flutter service for DataNarrative API

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'models.dart';

/// Main service class for DataNarrative API
class DataNarrativeService {
  final String baseUrl;
  final http.Client _client;
  
  DataNarrativeService({
    this.baseUrl = 'http://localhost:8000',
    http.Client? client,
  }) : _client = client ?? http.Client();
  
  /// Get full URL for an endpoint
  String _url(String endpoint) => '$baseUrl/api/v1$endpoint';
  
  /// Get full image URL
  String getImageUrl(String path) {
    if (path.startsWith('http')) return path;
    return '$baseUrl$path';
  }
  
  // ============================================================
  // QUERY ENDPOINTS
  // ============================================================
  
  /// Process a natural language query
  /// 
  /// Returns insights and optionally an infographic
  Future<QueryResponse> processQuery(
    String query, {
    String? domainHint,
    String? forceMode,
    bool includeImage = true,
  }) async {
    final response = await _client.post(
      Uri.parse(_url('/query')),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'query': query,
        'domain_hint': domainHint,
        'force_mode': forceMode,
        'include_image': includeImage,
      }),
    );
    
    if (response.statusCode != 200) {
      throw DataNarrativeException(
        'Query failed: ${response.statusCode}',
        response.body,
      );
    }
    
    return QueryResponse.fromJson(jsonDecode(response.body));
  }
  
  /// Analyze a query without generating results
  Future<Map<String, dynamic>> analyzeQuery(String query) async {
    final response = await _client.get(
      Uri.parse(_url('/query/analyze?q=${Uri.encodeComponent(query)}')),
    );
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Analysis failed', response.body);
    }
    
    return jsonDecode(response.body);
  }
  
  /// Get suggested queries
  Future<List<String>> getSuggestions({String? domain}) async {
    String url = _url('/query/suggestions');
    if (domain != null) url += '?domain=$domain';
    
    final response = await _client.get(Uri.parse(url));
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Failed to get suggestions', response.body);
    }
    
    final data = jsonDecode(response.body);
    return List<String>.from(data['suggestions'] ?? []);
  }
  
  /// Get query history
  Future<List<Map<String, dynamic>>> getQueryHistory({
    int limit = 20,
    String? status,
  }) async {
    String url = _url('/query/history?limit=$limit');
    if (status != null) url += '&status=$status';
    
    final response = await _client.get(Uri.parse(url));
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Failed to get history', response.body);
    }
    
    final data = jsonDecode(response.body);
    return List<Map<String, dynamic>>.from(data['items'] ?? []);
  }
  
  // ============================================================
  // RENDER ENDPOINTS
  // ============================================================
  
  /// Render an infographic manually
  Future<RenderResponse> renderManual({
    required String title,
    String template = 'hero_stat',
    String outputMode = 'data',
    String? subtitle,
    List<Map<String, dynamic>>? metrics,
    List<Map<String, dynamic>>? chartData,
    List<String>? insights,
    List<Map<String, dynamic>>? narrativeFrames,
    String domain = 'general',
    String sentiment = 'neutral',
    String? source,
    String? timePeriod,
  }) async {
    final response = await _client.post(
      Uri.parse(_url('/render/manual')),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'template': template,
        'output_mode': outputMode,
        'title': title,
        'subtitle': subtitle,
        'metrics': metrics,
        'chart_data': chartData,
        'insights': insights,
        'narrative_frames': narrativeFrames,
        'domain': domain,
        'sentiment': sentiment,
        'source': source,
        'time_period': timePeriod,
      }),
    );
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Render failed', response.body);
    }
    
    return RenderResponse.fromJson(jsonDecode(response.body));
  }
  
  /// Quick render for simple metrics
  Future<RenderResponse> quickRender({
    required String title,
    required num value,
    required String label,
    double? change,
    String domain = 'general',
    String template = 'hero_stat',
  }) async {
    String url = _url('/render/quick'
        '?title=${Uri.encodeComponent(title)}'
        '&value=$value'
        '&label=${Uri.encodeComponent(label)}'
        '&domain=$domain'
        '&template=$template');
    
    if (change != null) url += '&change=$change';
    
    final response = await _client.post(Uri.parse(url));
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Quick render failed', response.body);
    }
    
    return RenderResponse.fromJson(jsonDecode(response.body));
  }
  
  /// Get available templates
  Future<List<TemplateInfo>> getTemplates() async {
    final response = await _client.get(Uri.parse(_url('/render/templates')));
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Failed to get templates', response.body);
    }
    
    final data = jsonDecode(response.body) as List;
    return data.map((e) => TemplateInfo.fromJson(e)).toList();
  }
  
  /// Get infogram details
  Future<Map<String, dynamic>> getInfogram(String infogramId) async {
    final response = await _client.get(
      Uri.parse(_url('/render/infogram/$infogramId')),
    );
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Infogram not found', response.body);
    }
    
    return jsonDecode(response.body);
  }
  
  /// Update infogram status (approve/reject)
  Future<void> updateInfogramStatus(
    String infogramId,
    String status, {
    String? approvedBy,
  }) async {
    String url = _url('/render/infogram/$infogramId/status?status=$status');
    if (approvedBy != null) url += '&approved_by=${Uri.encodeComponent(approvedBy)}';
    
    final response = await _client.patch(Uri.parse(url));
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Status update failed', response.body);
    }
  }
  
  /// Get approval queue
  Future<List<Map<String, dynamic>>> getApprovalQueue({
    String status = 'pending',
    int limit = 20,
  }) async {
    final response = await _client.get(
      Uri.parse(_url('/render/queue?status=$status&limit=$limit')),
    );
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Failed to get queue', response.body);
    }
    
    final data = jsonDecode(response.body);
    return List<Map<String, dynamic>>.from(data['items'] ?? []);
  }
  
  // ============================================================
  // INGEST ENDPOINTS
  // ============================================================
  
  /// Upload a file to the knowledge base
  Future<IngestResult> uploadFile(
    File file,
    String sourceName, {
    String? domainHint,
    String? description,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse(_url('/ingest/upload')),
    );
    
    request.files.add(await http.MultipartFile.fromPath('file', file.path));
    request.fields['source_name'] = sourceName;
    if (domainHint != null) request.fields['domain_hint'] = domainHint;
    if (description != null) request.fields['description'] = description;
    
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Upload failed', response.body);
    }
    
    return IngestResult.fromJson(jsonDecode(response.body));
  }
  
  /// Ingest manual data
  Future<IngestResult> ingestManualData({
    required String sourceName,
    required List<Map<String, dynamic>> data,
    String? domain,
    List<String>? columns,
    String? description,
  }) async {
    final response = await _client.post(
      Uri.parse(_url('/ingest/manual')),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'source_name': sourceName,
        'data': data,
        'domain': domain,
        'columns': columns,
        'description': description,
      }),
    );
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Ingest failed', response.body);
    }
    
    return IngestResult.fromJson(jsonDecode(response.body));
  }
  
  /// List data sources
  Future<List<Map<String, dynamic>>> listSources({
    String? domain,
    String? status,
  }) async {
    String url = _url('/ingest/sources');
    List<String> params = [];
    if (domain != null) params.add('domain=$domain');
    if (status != null) params.add('status=$status');
    if (params.isNotEmpty) url += '?${params.join('&')}';
    
    final response = await _client.get(Uri.parse(url));
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Failed to list sources', response.body);
    }
    
    final data = jsonDecode(response.body);
    return List<Map<String, dynamic>>.from(data['sources'] ?? []);
  }
  
  /// Get knowledge base stats
  Future<Map<String, dynamic>> getKnowledgeStats() async {
    final response = await _client.get(Uri.parse(_url('/ingest/stats')));
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Failed to get stats', response.body);
    }
    
    return jsonDecode(response.body);
  }
  
  /// Delete a data source
  Future<void> deleteSource(String sourceId) async {
    final response = await _client.delete(
      Uri.parse(_url('/ingest/sources/$sourceId')),
    );
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Delete failed', response.body);
    }
  }
  
  // ============================================================
  // UTILITY ENDPOINTS
  // ============================================================
  
  /// Health check
  Future<Map<String, dynamic>> healthCheck() async {
    final response = await _client.get(Uri.parse('$baseUrl/health'));
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Health check failed', response.body);
    }
    
    return jsonDecode(response.body);
  }
  
  /// Get config
  Future<Map<String, dynamic>> getConfig() async {
    final response = await _client.get(Uri.parse(_url('/config')));
    
    if (response.statusCode != 200) {
      throw DataNarrativeException('Failed to get config', response.body);
    }
    
    return jsonDecode(response.body);
  }
  
  /// Close the client
  void dispose() {
    _client.close();
  }
}

/// Custom exception for DataNarrative errors
class DataNarrativeException implements Exception {
  final String message;
  final String? details;
  
  DataNarrativeException(this.message, [this.details]);
  
  @override
  String toString() => 'DataNarrativeException: $message${details != null ? '\nDetails: $details' : ''}';
}
