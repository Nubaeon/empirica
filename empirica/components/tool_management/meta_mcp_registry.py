#!/usr/bin/env python3
"""
Meta-MCP Registry - Personal Tool Registry with Epistemic Mapping

This is the AI's personal knowledge about tools and MCP servers, living in
the self-awareness layer. It learns which tools work for which epistemic gaps.

Key Principles:
1. AI manages its own tools (no manual loading every time)
2. Tools mapped to epistemic vectors (evidence-based)
3. Learns from experience (success patterns)
4. Discovers new tools online (multi-source)
5. Domain-specific specialization (agent roles)

Architecture:
    Self-Awareness Layer (Trusted)
    ├── Meta-MCP Registry (this)
    │   ├── Discovered MCP servers
    │   ├── Epistemic → Tool mapping (learned)
    │   ├── Success patterns per AI
    │   └── Domain specialization
    └── External MCP Servers
        └── Invoked via MCP client

This is NOT redundant with MCP - it's the INTELLIGENCE LAYER.
MCP = what tools exist (stateless)
Meta-MCP = what works for ME (stateful, learned)
"""

import json
import time
import asyncio
import requests
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import logging

# Try to import canonical components
try:
    from canonical.reflex_frame import EpistemicAssessment
    CANONICAL_AVAILABLE = True
except ImportError:
    CANONICAL_AVAILABLE = False
    # Create placeholder for type hints
    EpistemicAssessment = Any


class ToolSource(Enum):
    """Where a tool was discovered from"""
    BUILTIN = "builtin"
    GITHUB = "github"
    NPM = "npm"
    PYPI = "pypi"
    ANTHROPIC_REGISTRY = "anthropic_registry"
    MANUAL = "manual"
    SHARED = "shared"  # From another AI


class EpistemicVectorType(Enum):
    """Epistemic vectors from canonical assessment"""
    KNOW = "know"
    DO = "do"
    CONTEXT = "context"
    CLARITY = "clarity"
    COHERENCE = "coherence"
    SIGNAL = "signal"
    DENSITY = "density"
    STATE = "state"
    CHANGE = "change"
    COMPLETION = "completion"
    IMPACT = "impact"
    ENGAGEMENT = "engagement"


@dataclass
class MCPServer:
    """A discovered MCP server"""
    id: str
    name: str
    url: str
    description: str
    source: ToolSource
    
    # Discovery metadata
    discovered_at: float
    github_url: Optional[str] = None
    stars: int = 0
    last_updated: Optional[str] = None
    
    # Tool information
    available_tools: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    
    # Learning data
    usage_count: int = 0
    success_count: int = 0
    last_used: Optional[float] = None
    
    # Epistemic mapping (learned)
    helped_vectors: Dict[str, float] = field(default_factory=dict)  # vector → improvement
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'source': self.source.value,
            'discovered_at': self.discovered_at,
            'github_url': self.github_url,
            'stars': self.stars,
            'last_updated': self.last_updated,
            'available_tools': self.available_tools,
            'use_cases': self.use_cases,
            'usage_count': self.usage_count,
            'success_count': self.success_count,
            'last_used': self.last_used,
            'helped_vectors': self.helped_vectors,
            'success_rate': self.success_rate()
        }


@dataclass
class EpistemicToolMapping:
    """Mapping between epistemic gap and tool effectiveness"""
    vector: EpistemicVectorType
    score_threshold: float  # When vector is below this, tool is relevant
    tool_server_id: str
    tool_name: str
    
    # Learning data
    times_used: int = 0
    times_helped: int = 0
    average_improvement: float = 0.0
    last_used: Optional[float] = None
    
    # Context factors (when does this work?)
    works_for_domains: List[str] = field(default_factory=list)
    works_for_contexts: List[str] = field(default_factory=list)
    
    def effectiveness(self) -> float:
        """Calculate effectiveness score"""
        if self.times_used == 0:
            return 0.0
        help_rate = self.times_helped / self.times_used
        return (help_rate * 0.7) + (self.average_improvement * 0.3)


class MetaMCPRegistry:
    """
    Personal tool registry with epistemic mapping
    Lives in the AI's self-awareness layer
    """
    
    def __init__(self, 
                 ai_id: str,
                 registry_dir: Optional[str] = None,
                 domain: Optional[str] = None,
                 agent_role: Optional[str] = None):
        """
        Initialize Meta-MCP Registry
        
        Args:
            ai_id: Unique identifier for this AI
            registry_dir: Directory for persistent storage
            domain: Domain specialization (e.g., 'security_auditing')
            agent_role: Agent role (e.g., 'security_specialist')
        """
        self.ai_id = ai_id
        self.domain = domain
        self.agent_role = agent_role
        
        # Set up persistence
        if registry_dir:
            self.registry_dir = Path(registry_dir)
        else:
            default_dir = Path(__file__).parent.parent / '.meta_mcp_registry' / ai_id
            self.registry_dir = default_dir
        
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        # Registry state
        self.mcp_servers: Dict[str, MCPServer] = {}
        self.epistemic_mappings: List[EpistemicToolMapping] = []
        
        # Discovery sources (from enhanced_online_discovery.py patterns)
        self.discovery_sources = {
            "github": "https://api.github.com/search/repositories",
            "npm": "https://registry.npmjs.org/-/v1/search",
            "pypi": "https://pypi.org/pypi",
            "anthropic_registry": "https://mcp.anthropic.com/registry"
        }
        
        # Domain knowledge
        self.domain_specialization = {}
        self.epistemic_strengths = {}  # My strong vectors
        
        # Statistics
        self.total_discoveries = 0
        self.total_invocations = 0
        self.total_learning_updates = 0
        
        # Load existing registry
        self.load_registry()
        
        logging.info(f"📚 Meta-MCP Registry initialized for {ai_id}")
        if domain:
            logging.info(f"   🎯 Domain: {domain}")
        if agent_role:
            logging.info(f"   👤 Role: {agent_role}")
    
    # ========================================================================
    # DISCOVERY: Finding new MCP servers
    # ========================================================================
    
    async def discover_online_servers(self, 
                                      search_context: Optional[Dict[str, Any]] = None) -> List[MCPServer]:
        """
        Discover MCP servers from online sources
        
        Pattern from: enhanced_online_discovery.py
        Searches: GitHub, NPM, PyPI, Anthropic registry
        """
        logging.info("🌐 Discovering MCP servers online...")
        
        if not search_context:
            search_context = self._generate_search_context()
        
        discovered_servers = []
        
        # Search GitHub
        github_servers = await self._search_github(search_context)
        discovered_servers.extend(github_servers)
        
        # Search NPM
        npm_servers = await self._search_npm(search_context)
        discovered_servers.extend(npm_servers)
        
        # Search Anthropic registry
        anthropic_servers = await self._search_anthropic_registry(search_context)
        discovered_servers.extend(anthropic_servers)
        
        # Register discovered servers
        for server in discovered_servers:
            self.register_server(server)
        
        self.total_discoveries += len(discovered_servers)
        self.save_registry()
        
        logging.info(f"✅ Discovered {len(discovered_servers)} new MCP servers")
        return discovered_servers
    
    async def _search_github(self, context: Dict[str, Any]) -> List[MCPServer]:
        """Search GitHub for MCP servers"""
        servers = []
        
        search_terms = [
            "mcp server",
            "model context protocol",
            "anthropic mcp",
            "claude tools"
        ]
        
        # Add domain-specific search terms
        if self.domain:
            search_terms.append(f"mcp {self.domain}")
        
        for term in search_terms[:2]:  # Limit searches
            try:
                query = f"{term} language:python OR language:typescript"
                response = requests.get(
                    self.discovery_sources["github"],
                    params={'q': query, 'sort': 'stars', 'order': 'desc', 'per_page': 5},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for repo in data.get('items', []):
                        if self._is_likely_mcp_server(repo):
                            server = MCPServer(
                                id=repo['full_name'].lower().replace('/', '-'),
                                name=repo['name'],
                                url=repo['html_url'],
                                description=repo.get('description', ''),
                                source=ToolSource.GITHUB,
                                discovered_at=time.time(),
                                github_url=repo['html_url'],
                                stars=repo.get('stargazers_count', 0),
                                last_updated=repo.get('updated_at')
                            )
                            servers.append(server)
                            
            except Exception as e:
                logging.error(f"GitHub search error: {e}")
        
        return servers
    
    async def _search_npm(self, context: Dict[str, Any]) -> List[MCPServer]:
        """Search NPM for MCP servers"""
        servers = []
        
        try:
            response = requests.get(
                self.discovery_sources["npm"],
                params={'text': 'mcp server', 'size': 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                for pkg in data.get('objects', []):
                    package = pkg.get('package', {})
                    if self._is_likely_npm_mcp_server(package):
                        server = MCPServer(
                            id=package['name'].lower().replace('@', '').replace('/', '-'),
                            name=package['name'],
                            url=package.get('links', {}).get('npm', ''),
                            description=package.get('description', ''),
                            source=ToolSource.NPM,
                            discovered_at=time.time(),
                            github_url=package.get('links', {}).get('repository'),
                            stars=0  # NPM doesn't provide stars
                        )
                        servers.append(server)
                        
        except Exception as e:
            logging.error(f"NPM search error: {e}")
        
        return servers
    
    async def _search_anthropic_registry(self, context: Dict[str, Any]) -> List[MCPServer]:
        """Search Anthropic's official MCP registry"""
        servers = []
        
        try:
            response = requests.get(
                self.discovery_sources["anthropic_registry"],
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                for server_info in data.get('servers', []):
                    server = MCPServer(
                        id=server_info['id'],
                        name=server_info['name'],
                        url=server_info['url'],
                        description=server_info.get('description', ''),
                        source=ToolSource.ANTHROPIC_REGISTRY,
                        discovered_at=time.time(),
                        available_tools=server_info.get('tools', []),
                        use_cases=server_info.get('use_cases', [])
                    )
                    servers.append(server)
                    
        except Exception as e:
            logging.error(f"Anthropic registry search error: {e}")
        
        return servers
    
    def _generate_search_context(self) -> Dict[str, Any]:
        """Generate search context based on AI's state"""
        return {
            'ai_id': self.ai_id,
            'domain': self.domain,
            'agent_role': self.agent_role,
            'current_servers': list(self.mcp_servers.keys()),
            'epistemic_strengths': self.epistemic_strengths,
            'priority_vectors': self._get_weak_vectors()
        }
    
    def _is_likely_mcp_server(self, repo: Dict[str, Any]) -> bool:
        """Check if GitHub repo is likely an MCP server"""
        name = repo.get('name', '').lower()
        desc = repo.get('description', '').lower()
        
        mcp_indicators = ['mcp', 'model context protocol', 'claude', 'anthropic']
        return any(indicator in name or indicator in desc for indicator in mcp_indicators)
    
    def _is_likely_npm_mcp_server(self, package: Dict[str, Any]) -> bool:
        """Check if NPM package is likely an MCP server"""
        name = package.get('name', '').lower()
        keywords = package.get('keywords', [])
        
        mcp_keywords = ['mcp', 'model-context-protocol', 'claude', 'anthropic']
        return any(kw in mcp_keywords for kw in keywords) or 'mcp' in name
    
    # ========================================================================
    # EPISTEMIC MAPPING: Learning which tools help which vectors
    # ========================================================================
    
    def register_server(self, server: MCPServer):
        """Register a newly discovered server"""
        self.mcp_servers[server.id] = server
        logging.info(f"📚 Registered: {server.name} ({server.source.value})")
    
    async def recommend_for_epistemic_gap(self,
                                          assessment: EpistemicAssessment,
                                          context: Optional[Dict[str, Any]] = None) -> List[Tuple[MCPServer, str, float]]:
        """
        Recommend MCP servers/tools for epistemic gaps
        
        Returns: List of (server, tool_name, confidence) tuples
        Based on learned patterns of what helps which vectors
        """
        recommendations = []
        
        # Identify gaps (vectors below threshold)
        gaps = self._identify_epistemic_gaps(assessment)
        
        for vector, score in gaps:
            # Find mappings that have helped this vector before
            relevant_mappings = [
                m for m in self.epistemic_mappings
                if m.vector.value == vector and m.score_threshold >= score
            ]
            
            # Sort by effectiveness
            relevant_mappings.sort(key=lambda m: m.effectiveness(), reverse=True)
            
            # Get top recommendations
            for mapping in relevant_mappings[:3]:
                server = self.mcp_servers.get(mapping.tool_server_id)
                if server:
                    confidence = mapping.effectiveness()
                    recommendations.append((server, mapping.tool_name, confidence))
        
        # If no learned mappings, explore
        if not recommendations:
            recommendations = await self._explore_new_tools(gaps, context)
        
        return recommendations
    
    def _identify_epistemic_gaps(self, assessment: EpistemicAssessment) -> List[Tuple[str, float]]:
        """Identify which vectors are below threshold (gaps)"""
        gaps = []
        threshold = 0.70
        
        vectors = {
            'know': assessment.know.score,
            'do': assessment.do.score,
            'context': assessment.context.score,
            'clarity': assessment.clarity.score,
            'coherence': assessment.coherence.score,
            'signal': assessment.signal.score,
            'density': assessment.density.score,
            'state': assessment.state.score,
            'change': assessment.change.score,
            'completion': assessment.completion.score,
            'impact': assessment.impact.score,
            'engagement': assessment.engagement.score
        }
        
        for vector_name, score in vectors.items():
            if score < threshold:
                gaps.append((vector_name, score))
        
        # Sort by severity (lowest scores first)
        gaps.sort(key=lambda x: x[1])
        
        return gaps
    
    async def _explore_new_tools(self, 
                                gaps: List[Tuple[str, float]], 
                                context: Optional[Dict[str, Any]]) -> List[Tuple[MCPServer, str, float]]:
        """
        Exploration mode: Try new tools for gaps we haven't seen before
        """
        recommendations = []
        
        # Use simple heuristics for exploration
        for vector, score in gaps[:2]:  # Top 2 gaps
            # Get servers that mention relevant keywords
            relevant_servers = self._find_servers_by_keyword(vector)
            
            for server in relevant_servers[:2]:
                # Low confidence (exploration)
                recommendations.append((server, "explore", 0.3))
        
        return recommendations
    
    def _find_servers_by_keyword(self, vector: str) -> List[MCPServer]:
        """Find servers whose description mentions the vector"""
        keyword_map = {
            'know': ['documentation', 'search', 'knowledge', 'wiki'],
            'do': ['execute', 'run', 'test', 'simulate'],
            'context': ['workspace', 'environment', 'system', 'git'],
            'clarity': ['clarify', 'explain', 'define'],
            'state': ['status', 'state', 'monitor']
        }
        
        keywords = keyword_map.get(vector, [])
        relevant_servers = []
        
        for server in self.mcp_servers.values():
            desc_lower = server.description.lower()
            if any(kw in desc_lower for kw in keywords):
                relevant_servers.append(server)
        
        return relevant_servers
    
    async def learn_from_usage(self,
                              server_id: str,
                              tool_name: str,
                              vector_before: str,
                              score_before: float,
                              score_after: float,
                              success: bool):
        """
        Learn from tool usage - update epistemic mappings
        
        This is the core learning mechanism: evidence-based pattern learning
        """
        server = self.mcp_servers.get(server_id)
        if not server:
            return
        
        # Update server statistics
        server.usage_count += 1
        server.last_used = time.time()
        if success:
            server.success_count += 1
        
        # Calculate improvement
        improvement = score_after - score_before
        
        # Update/create epistemic mapping
        mapping = self._find_or_create_mapping(
            vector_before,
            score_before,
            server_id,
            tool_name
        )
        
        mapping.times_used += 1
        if improvement > 0.05:  # Significant improvement
            mapping.times_helped += 1
        
        # Update average improvement (exponential moving average)
        alpha = 0.3  # Learning rate
        mapping.average_improvement = (
            alpha * improvement + (1 - alpha) * mapping.average_improvement
        )
        mapping.last_used = time.time()
        
        # Update server's helped_vectors
        if vector_before not in server.helped_vectors:
            server.helped_vectors[vector_before] = improvement
        else:
            # Exponential moving average
            server.helped_vectors[vector_before] = (
                alpha * improvement + (1 - alpha) * server.helped_vectors[vector_before]
            )
        
        self.total_learning_updates += 1
        self.save_registry()
        
        logging.info(f"📊 Learned: {server.name}/{tool_name} → {vector_before} (+{improvement:.2f})")
    
    def _find_or_create_mapping(self,
                               vector: str,
                               threshold: float,
                               server_id: str,
                               tool_name: str) -> EpistemicToolMapping:
        """Find existing mapping or create new one"""
        # Discretize threshold (round to nearest 0.1)
        threshold_bucket = round(threshold * 10) / 10
        
        # Look for existing mapping
        for mapping in self.epistemic_mappings:
            if (mapping.vector.value == vector and
                mapping.tool_server_id == server_id and
                mapping.tool_name == tool_name):
                return mapping
        
        # Create new mapping
        try:
            vector_enum = EpistemicVectorType(vector)
        except ValueError:
            vector_enum = EpistemicVectorType.KNOW  # Default
        
        mapping = EpistemicToolMapping(
            vector=vector_enum,
            score_threshold=threshold_bucket,
            tool_server_id=server_id,
            tool_name=tool_name
        )
        
        self.epistemic_mappings.append(mapping)
        return mapping
    
    def _get_weak_vectors(self) -> List[str]:
        """Get vectors that are typically weak (for search context)"""
        # This would be based on historical assessments
        # For now, return common gaps
        return ['know', 'context', 'clarity']
    
    # ========================================================================
    # PERSISTENCE: Save and load registry
    # ========================================================================
    
    def save_registry(self):
        """Save registry to disk"""
        registry_file = self.registry_dir / 'registry.json'
        
        data = {
            'ai_id': self.ai_id,
            'domain': self.domain,
            'agent_role': self.agent_role,
            'servers': {sid: server.to_dict() for sid, server in self.mcp_servers.items()},
            'epistemic_mappings': [
                {
                    'vector': m.vector.value,
                    'score_threshold': m.score_threshold,
                    'tool_server_id': m.tool_server_id,
                    'tool_name': m.tool_name,
                    'times_used': m.times_used,
                    'times_helped': m.times_helped,
                    'average_improvement': m.average_improvement,
                    'last_used': m.last_used
                }
                for m in self.epistemic_mappings
            ],
            'statistics': {
                'total_discoveries': self.total_discoveries,
                'total_invocations': self.total_invocations,
                'total_learning_updates': self.total_learning_updates
            },
            'last_saved': time.time()
        }
        
        with open(registry_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_registry(self):
        """Load registry from disk"""
        registry_file = self.registry_dir / 'registry.json'
        
        if not registry_file.exists():
            logging.info("📚 No existing registry found, starting fresh")
            return
        
        try:
            with open(registry_file, 'r') as f:
                data = json.load(f)
            
            # Load servers
            for server_data in data.get('servers', {}).values():
                server = MCPServer(
                    id=server_data['id'],
                    name=server_data['name'],
                    url=server_data['url'],
                    description=server_data['description'],
                    source=ToolSource(server_data['source']),
                    discovered_at=server_data['discovered_at'],
                    github_url=server_data.get('github_url'),
                    stars=server_data.get('stars', 0),
                    last_updated=server_data.get('last_updated'),
                    available_tools=server_data.get('available_tools', []),
                    use_cases=server_data.get('use_cases', []),
                    usage_count=server_data.get('usage_count', 0),
                    success_count=server_data.get('success_count', 0),
                    last_used=server_data.get('last_used'),
                    helped_vectors=server_data.get('helped_vectors', {})
                )
                self.mcp_servers[server.id] = server
            
            # Load epistemic mappings
            for mapping_data in data.get('epistemic_mappings', []):
                mapping = EpistemicToolMapping(
                    vector=EpistemicVectorType(mapping_data['vector']),
                    score_threshold=mapping_data['score_threshold'],
                    tool_server_id=mapping_data['tool_server_id'],
                    tool_name=mapping_data['tool_name'],
                    times_used=mapping_data.get('times_used', 0),
                    times_helped=mapping_data.get('times_helped', 0),
                    average_improvement=mapping_data.get('average_improvement', 0.0),
                    last_used=mapping_data.get('last_used')
                )
                self.epistemic_mappings.append(mapping)
            
            # Load statistics
            stats = data.get('statistics', {})
            self.total_discoveries = stats.get('total_discoveries', 0)
            self.total_invocations = stats.get('total_invocations', 0)
            self.total_learning_updates = stats.get('total_learning_updates', 0)
            
            logging.info(f"📚 Loaded registry: {len(self.mcp_servers)} servers, {len(self.epistemic_mappings)} mappings")
            
        except Exception as e:
            logging.error(f"Failed to load registry: {e}")
    
    # ========================================================================
    # INTROSPECTION: Understanding the registry
    # ========================================================================
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of registry state"""
        return {
            'ai_id': self.ai_id,
            'domain': self.domain,
            'agent_role': self.agent_role,
            'total_servers': len(self.mcp_servers),
            'total_mappings': len(self.epistemic_mappings),
            'total_discoveries': self.total_discoveries,
            'total_invocations': self.total_invocations,
            'total_learning_updates': self.total_learning_updates,
            'top_servers': [
                {
                    'name': s.name,
                    'usage_count': s.usage_count,
                    'success_rate': s.success_rate()
                }
                for s in sorted(self.mcp_servers.values(), key=lambda x: x.usage_count, reverse=True)[:5]
            ],
            'best_mappings': [
                {
                    'vector': m.vector.value,
                    'server': self.mcp_servers[m.tool_server_id].name if m.tool_server_id in self.mcp_servers else 'unknown',
                    'tool': m.tool_name,
                    'effectiveness': m.effectiveness()
                }
                for m in sorted(self.epistemic_mappings, key=lambda x: x.effectiveness(), reverse=True)[:5]
            ]
        }


# Convenience function
def create_meta_mcp_registry(ai_id: str, 
                            domain: Optional[str] = None,
                            agent_role: Optional[str] = None) -> MetaMCPRegistry:
    """Create and return a MetaMCPRegistry instance"""
    return MetaMCPRegistry(ai_id, domain=domain, agent_role=agent_role)


if __name__ == "__main__":
    # Test the Meta-MCP Registry
    print("📚 Testing Meta-MCP Registry\n")
    
    async def test_registry():
        registry = MetaMCPRegistry(
            ai_id="test_ai_001",
            domain="code_analysis"
        )
        
        print(f"✅ Registry initialized for {registry.ai_id}")
        print(f"   Domain: {registry.domain}")
        
        # Test discovery
        print("\n🌐 Running online discovery...")
        discovered = await registry.discover_online_servers()
        print(f"✅ Discovered {len(discovered)} servers")
        
        # Show summary
        summary = registry.get_registry_summary()
        print(f"\n📊 Registry Summary:")
        print(f"   Total servers: {summary['total_servers']}")
        print(f"   Total mappings: {summary['total_mappings']}")
        
        print("\n✅ Meta-MCP Registry test complete!")
    
    asyncio.run(test_registry())
