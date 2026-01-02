/// Query Input Widget
/// ==================
/// Natural language input for DataNarrative queries

import 'package:flutter/material.dart';

/// Query input widget with suggestions
class QueryInput extends StatefulWidget {
  final Function(String query) onSubmit;
  final List<String> suggestions;
  final bool isLoading;
  final String? placeholder;
  
  const QueryInput({
    Key? key,
    required this.onSubmit,
    this.suggestions = const [],
    this.isLoading = false,
    this.placeholder,
  }) : super(key: key);
  
  @override
  State<QueryInput> createState() => _QueryInputState();
}

class _QueryInputState extends State<QueryInput> {
  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  bool _showSuggestions = false;
  
  @override
  void initState() {
    super.initState();
    _focusNode.addListener(() {
      setState(() => _showSuggestions = _focusNode.hasFocus);
    });
  }
  
  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }
  
  void _submit() {
    final query = _controller.text.trim();
    if (query.isNotEmpty) {
      widget.onSubmit(query);
      _focusNode.unfocus();
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Input field
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: TextField(
            controller: _controller,
            focusNode: _focusNode,
            enabled: !widget.isLoading,
            decoration: InputDecoration(
              hintText: widget.placeholder ?? 'Ask about your data...',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: widget.isLoading
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
                      onPressed: _submit,
                    ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              filled: true,
              fillColor: Colors.white,
              contentPadding: const EdgeInsets.all(16),
            ),
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _submit(),
          ),
        ),
        
        // Suggestions
        if (_showSuggestions && widget.suggestions.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(top: 8),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 5,
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                  child: Text(
                    'Try asking:',
                    style: TextStyle(
                      color: Colors.grey.shade600,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                ...widget.suggestions.take(5).map((suggestion) => InkWell(
                  onTap: () {
                    _controller.text = suggestion;
                    _submit();
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 10,
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.lightbulb_outline,
                          size: 18,
                          color: Colors.amber.shade700,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            suggestion,
                            style: const TextStyle(fontSize: 14),
                          ),
                        ),
                        Icon(
                          Icons.arrow_forward_ios,
                          size: 14,
                          color: Colors.grey.shade400,
                        ),
                      ],
                    ),
                  ),
                )),
                const SizedBox(height: 8),
              ],
            ),
          ),
      ],
    );
  }
}

/// Domain selector chips
class DomainSelector extends StatelessWidget {
  final String? selectedDomain;
  final Function(String?) onChanged;
  final List<String> domains;
  
  const DomainSelector({
    Key? key,
    required this.selectedDomain,
    required this.onChanged,
    this.domains = const [
      'education',
      'health',
      'economy',
      'agriculture',
    ],
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          // All domains chip
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: const Text('All'),
              selected: selectedDomain == null,
              onSelected: (selected) {
                if (selected) onChanged(null);
              },
            ),
          ),
          // Domain chips
          ...domains.map((domain) => Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(_capitalize(domain)),
              selected: selectedDomain == domain,
              onSelected: (selected) {
                onChanged(selected ? domain : null);
              },
            ),
          )),
        ],
      ),
    );
  }
  
  String _capitalize(String s) =>
      s.isNotEmpty ? '${s[0].toUpperCase()}${s.substring(1)}' : s;
}
