/// Example Query Screen
/// ====================
/// Complete screen demonstrating DataNarrative integration

import 'package:flutter/material.dart';
// Import your widgets and service
// import '../datanarrative_service.dart';
// import '../models.dart';
// import '../widgets/query_input.dart';
// import '../widgets/infogram_viewer.dart';

/// Example home screen with query functionality
class DataNarrativeQueryScreen extends StatefulWidget {
  const DataNarrativeQueryScreen({Key? key}) : super(key: key);
  
  @override
  State<DataNarrativeQueryScreen> createState() => _DataNarrativeQueryScreenState();
}

class _DataNarrativeQueryScreenState extends State<DataNarrativeQueryScreen> {
  // final DataNarrativeService _service = DataNarrativeService(
  //   baseUrl: 'http://YOUR_SERVER:8000',
  // );
  
  bool _isLoading = false;
  String? _selectedDomain;
  List<String> _suggestions = [];
  // QueryResponse? _result;
  String? _errorMessage;
  
  @override
  void initState() {
    super.initState();
    _loadSuggestions();
  }
  
  Future<void> _loadSuggestions() async {
    // try {
    //   final suggestions = await _service.getSuggestions(domain: _selectedDomain);
    //   setState(() => _suggestions = suggestions);
    // } catch (e) {
    //   // Handle error
    // }
    
    // Demo suggestions
    setState(() {
      _suggestions = [
        'How has literacy changed in Telangana?',
        'Which district has the highest enrollment?',
        'Compare urban vs rural education',
        'Show teacher-student ratio trends',
      ];
    });
  }
  
  Future<void> _processQuery(String query) async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    
    // try {
    //   final result = await _service.processQuery(
    //     query,
    //     domainHint: _selectedDomain,
    //   );
    //   setState(() => _result = result);
    // } catch (e) {
    //   setState(() => _errorMessage = e.toString());
    // } finally {
    //   setState(() => _isLoading = false);
    // }
    
    // Demo: Simulate API call
    await Future.delayed(const Duration(seconds: 2));
    setState(() {
      _isLoading = false;
      // In real app, you'd have _result from API
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        title: const Text('DataNarrative'),
        centerTitle: true,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () {
              // Navigate to history screen
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor,
                borderRadius: const BorderRadius.only(
                  bottomLeft: Radius.circular(24),
                  bottomRight: Radius.circular(24),
                ),
              ),
              child: Column(
                children: [
                  const Text(
                    'Ask questions about your data',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // Query input (simplified demo version)
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: TextField(
                      enabled: !_isLoading,
                      decoration: InputDecoration(
                        hintText: 'How has literacy changed in Telangana?',
                        prefixIcon: const Icon(Icons.search),
                        suffixIcon: _isLoading
                            ? const Padding(
                                padding: EdgeInsets.all(12),
                                child: SizedBox(
                                  width: 24,
                                  height: 24,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                ),
                              )
                            : IconButton(
                                icon: const Icon(Icons.send),
                                onPressed: () => _processQuery('demo query'),
                              ),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.all(16),
                      ),
                      onSubmitted: _processQuery,
                    ),
                  ),
                  
                  const SizedBox(height: 12),
                  
                  // Domain chips
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: ['All', 'Education', 'Health', 'Economy'].map((d) {
                        final isSelected = (d == 'All' && _selectedDomain == null) ||
                            d.toLowerCase() == _selectedDomain;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ChoiceChip(
                            label: Text(d),
                            selected: isSelected,
                            onSelected: (selected) {
                              setState(() {
                                _selectedDomain = d == 'All' ? null : d.toLowerCase();
                              });
                              _loadSuggestions();
                            },
                            backgroundColor: Colors.white24,
                            selectedColor: Colors.white,
                            labelStyle: TextStyle(
                              color: isSelected ? Theme.of(context).primaryColor : Colors.white,
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
            
            // Content
            Expanded(
              child: _buildContent(),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildContent() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Analyzing your data...'),
          ],
        ),
      );
    }
    
    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(_errorMessage!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => setState(() => _errorMessage = null),
              child: const Text('Try Again'),
            ),
          ],
        ),
      );
    }
    
    // Show suggestions when no result
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Try asking:',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        ..._suggestions.map((s) => Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            leading: Icon(Icons.lightbulb_outline, color: Colors.amber.shade700),
            title: Text(s),
            trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            onTap: () => _processQuery(s),
          ),
        )),
        
        const SizedBox(height: 24),
        
        // Demo result placeholder
        Container(
          height: 400,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
              ),
            ],
          ),
          child: const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.bar_chart, size: 64, color: Colors.grey),
                SizedBox(height: 16),
                Text(
                  'Your infographic will appear here',
                  style: TextStyle(color: Colors.grey),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
