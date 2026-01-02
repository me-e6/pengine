/// Infogram Viewer Widget
/// ======================
/// Display DataNarrative infographics in your app

import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

/// Widget to display an infographic
class InfogramViewer extends StatelessWidget {
  final String imageUrl;
  final String? title;
  final VoidCallback? onTap;
  final VoidCallback? onApprove;
  final VoidCallback? onReject;
  final bool showActions;
  final BoxFit fit;
  
  const InfogramViewer({
    Key? key,
    required this.imageUrl,
    this.title,
    this.onTap,
    this.onApprove,
    this.onReject,
    this.showActions = false,
    this.fit = BoxFit.contain,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Title bar
          if (title != null)
            Container(
              padding: const EdgeInsets.all(12),
              color: Theme.of(context).primaryColor.withOpacity(0.1),
              child: Text(
                title!,
                style: Theme.of(context).textTheme.titleMedium,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          
          // Image
          Expanded(
            child: GestureDetector(
              onTap: onTap,
              child: CachedNetworkImage(
                imageUrl: imageUrl,
                fit: fit,
                placeholder: (context, url) => const Center(
                  child: CircularProgressIndicator(),
                ),
                errorWidget: (context, url, error) => const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 48, color: Colors.red),
                      SizedBox(height: 8),
                      Text('Failed to load image'),
                    ],
                  ),
                ),
              ),
            ),
          ),
          
          // Action buttons
          if (showActions)
            Container(
              padding: const EdgeInsets.all(8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  if (onReject != null)
                    TextButton.icon(
                      onPressed: onReject,
                      icon: const Icon(Icons.close, color: Colors.red),
                      label: const Text('Reject', style: TextStyle(color: Colors.red)),
                    ),
                  if (onApprove != null)
                    ElevatedButton.icon(
                      onPressed: onApprove,
                      icon: const Icon(Icons.check),
                      label: const Text('Approve'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

/// Widget to display story carousel
class StoryCarouselViewer extends StatefulWidget {
  final List<String> imageUrls;
  final String? title;
  
  const StoryCarouselViewer({
    Key? key,
    required this.imageUrls,
    this.title,
  }) : super(key: key);
  
  @override
  State<StoryCarouselViewer> createState() => _StoryCarouselViewerState();
}

class _StoryCarouselViewerState extends State<StoryCarouselViewer> {
  int _currentIndex = 0;
  final PageController _pageController = PageController();
  
  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Title
        if (widget.title != null)
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              widget.title!,
              style: Theme.of(context).textTheme.titleLarge,
            ),
          ),
        
        // Page view
        Expanded(
          child: PageView.builder(
            controller: _pageController,
            itemCount: widget.imageUrls.length,
            onPageChanged: (index) {
              setState(() => _currentIndex = index);
            },
            itemBuilder: (context, index) {
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: CachedNetworkImage(
                  imageUrl: widget.imageUrls[index],
                  fit: BoxFit.contain,
                  placeholder: (context, url) => const Center(
                    child: CircularProgressIndicator(),
                  ),
                  errorWidget: (context, url, error) => const Icon(Icons.error),
                ),
              );
            },
          ),
        ),
        
        // Indicators
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Previous button
              IconButton(
                onPressed: _currentIndex > 0
                    ? () => _pageController.previousPage(
                          duration: const Duration(milliseconds: 300),
                          curve: Curves.easeInOut,
                        )
                    : null,
                icon: const Icon(Icons.arrow_back_ios),
              ),
              
              // Dots
              Row(
                children: List.generate(
                  widget.imageUrls.length,
                  (index) => Container(
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: index == _currentIndex
                          ? Theme.of(context).primaryColor
                          : Colors.grey.shade300,
                    ),
                  ),
                ),
              ),
              
              // Next button
              IconButton(
                onPressed: _currentIndex < widget.imageUrls.length - 1
                    ? () => _pageController.nextPage(
                          duration: const Duration(milliseconds: 300),
                          curve: Curves.easeInOut,
                        )
                    : null,
                icon: const Icon(Icons.arrow_forward_ios),
              ),
            ],
          ),
        ),
        
        // Frame label
        Text(
          'Frame ${_currentIndex + 1} of ${widget.imageUrls.length}',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 8),
      ],
    );
  }
}
