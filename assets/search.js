// Client-side search functionality
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    const searchResults = document.createElement('div');
    searchResults.id = 'search-results';
    searchResults.className = 'absolute top-full left-0 right-0 mt-2 bg-slate-900 border border-slate-700 rounded-lg shadow-xl max-h-96 overflow-y-auto hidden z-50';
    searchInput.parentElement.appendChild(searchResults);

    // Search index with page content
    const searchIndex = [
        { title: 'Home', url: '/index.html', keywords: 'empirica epistemic ai metacognition cascade vectors self-aware mirror git' },
        { title: 'Getting Started', url: '/getting-started.html', keywords: 'install setup cli python mcp bootstrap preflight' },
        { title: 'Features', url: '/features.html', keywords: 'cascade vectors assessment goals handoffs calibration' },
        { title: 'Use Cases', url: '/use-cases.html', keywords: 'examples applications multi-day security teams' },
        { title: 'Epistemics', url: '/epistemics.html', keywords: 'vectors know do uncertainty context clarity coherence signal density state change completion impact calibration' },
        { title: 'API Reference', url: '/developers/api-reference.html', keywords: 'api documentation python mcp tools functions' },
        { title: 'Architecture', url: '/developers/architecture.html', keywords: 'system design components storage sqlite json git notes' },
        { title: 'CLI Interface', url: '/developers/cli-interface.html', keywords: 'command line interface bootstrap preflight postflight goals handoff' },
        { title: 'System Prompts', url: '/developers/system-prompts.html', keywords: 'prompts chat ai claude gemini qwen' },
        { title: 'Components', url: '/developers/components.html', keywords: 'modules system parts cascade assessment engine' },
        { title: 'Examples', url: '/examples.html', keywords: 'code samples tutorials demonstrations' },
        { title: 'FAQs', url: '/faqs.html', keywords: 'questions answers help frequently asked' },
        { title: 'MCP Integration', url: '/mcp-integration.html', keywords: 'model context protocol cursor windsurf antigravity' },
        { title: 'Contact', url: '/contact.html', keywords: 'support help contact email github' },
        { title: 'AI vs Agent', url: '/ai-vs-agent.html', keywords: 'patterns when to use difference' },
        { title: 'Skills', url: '/skills.html', keywords: 'capabilities abilities' },
        { title: 'Making Git Sexy', url: '/MAKING_GIT_SEXY_AGAIN.html', keywords: 'git version control metacognition' },
        { title: 'Unified Theory', url: '/unified-theory.html', keywords: 'epistemic infrastructure hallucination handoff accountability theory mathematics' },
        { title: 'Empirica Chat', url: '/empirica-chat.html', keywords: 'claude skill chat integration cascade workflow memory' },
        { title: 'Resources', url: '/resources.html', keywords: 'media videos audio diagrams svgs screenshots notebooklm presentations' },
    ];

    let debounceTimer;

    searchInput.addEventListener('input', function (e) {
        clearTimeout(debounceTimer);
        const query = e.target.value.toLowerCase().trim();

        if (query.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        debounceTimer = setTimeout(() => {
            // Search through index
            const results = searchIndex.filter(item => {
                const titleMatch = item.title.toLowerCase().includes(query);
                const keywordMatch = item.keywords.toLowerCase().includes(query);
                const urlMatch = item.url.toLowerCase().includes(query);
                return titleMatch || keywordMatch || urlMatch;
            }).slice(0, 8); // Limit to 8 results

            if (results.length > 0) {
                searchResults.innerHTML = results.map(result => {
                    // Highlight matching text
                    const titleHighlighted = result.title.replace(
                        new RegExp(query, 'gi'),
                        match => `<mark class="bg-indigo-500/30 text-white">${match}</mark>`
                    );

                    return `
                        <a href="${result.url}" class="block px-4 py-3 hover:bg-slate-800 transition-colors border-b border-slate-800 last:border-b-0">
                            <div class="font-semibold text-white">${titleHighlighted}</div>
                            <div class="text-sm text-slate-400">${result.url}</div>
                        </a>
                    `;
                }).join('');
                searchResults.classList.remove('hidden');
            } else {
                searchResults.innerHTML = `
                    <div class="px-4 py-3 text-slate-400 text-sm">
                        No results found for "${query}"
                    </div>
                `;
                searchResults.classList.remove('hidden');
            }
        }, 150); // Debounce 150ms
    });

    // Close search results when clicking outside
    document.addEventListener('click', function (e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });

    // Navigate with keyboard
    searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            searchResults.classList.add('hidden');
            searchInput.blur();
        } else if (e.key === 'Enter' && searchResults.children.length > 0) {
            // Navigate to first result
            const firstLink = searchResults.querySelector('a');
            if (firstLink) {
                window.location.href = firstLink.href;
            }
        }
    });
});
