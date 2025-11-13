"""
Component Commands - Component listing, explanation, and demonstration functionality
"""

import json
from ..cli_utils import print_component_status, handle_cli_error, format_component_list


def handle_list_command(args):
    """Handle list components command"""
    try:
        from empirica.bootstraps.extended_metacognitive_bootstrap import ExtendedMetacognitiveBootstrap
        
        print("📋 Listing Empirica semantic components...")
        
        # Get component registry
        registry = get_component_registry()
        
        # Filter components if specified
        component_filter = getattr(args, 'filter', None)
        show_details = getattr(args, 'details', False)
        tier_filter = getattr(args, 'tier', None)
        
        components = registry.get_components(
            component_filter=component_filter,
            tier_filter=tier_filter
        )
        
        # Display component list
        print(format_component_list(components, show_details=show_details))
        
        # Show tier breakdown
        if not tier_filter:
            tier_counts = {}
            for component in components:
                tier = component.get('tier', 'unknown')
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            if tier_counts:
                print("\n🏗️ Components by tier:")
                for tier, count in sorted(tier_counts.items()):
                    print(f"   • {tier}: {count} components")
        
        # Show filter summary
        if component_filter or tier_filter:
            print(f"\n🔍 Filter applied:")
            if component_filter:
                print(f"   • Component filter: {component_filter}")
            if tier_filter:
                print(f"   • Tier filter: {tier_filter}")
        
        # Show component categories
        if show_details:
            categories = {}
            for component in components:
                category = component.get('category', 'uncategorized')
                if category not in categories:
                    categories[category] = []
                categories[category].append(component['name'])
            
            if categories:
                print("\n📂 Components by category:")
                for category, comp_list in sorted(categories.items()):
                    print(f"   📁 {category} ({len(comp_list)}):")
                    for comp in comp_list:
                        print(f"     • {comp}")
        
    except Exception as e:
        handle_cli_error(e, "List components", getattr(args, 'verbose', False))


def handle_explain_command(args):
    """Handle explain component command"""
    try:
        from empirica.bootstraps.extended_metacognitive_bootstrap import ExtendedMetacognitiveBootstrap
        
        component_name = args.component
        print(f"📖 Explaining component: {component_name}")
        
        # Get component registry
        registry = get_component_registry()
        component = registry.get_component(component_name)
        
        if not component:
            print(f"❌ Component '{component_name}' not found")
            
            # Suggest similar components
            similar = registry.find_similar_components(component_name)
            if similar:
                print("💡 Did you mean:")
                for suggestion in similar[:3]:
                    print(f"   • {suggestion}")
            return
        
        # Display component information
        print(f"✅ Component found: {component['name']}")
        print(f"   📂 Category: {component.get('category', 'unknown')}")
        print(f"   🏗️ Tier: {component.get('tier', 'unknown')}")
        print(f"   📊 Status: {component.get('status', 'unknown')}")
        
        # Show description
        if component.get('description'):
            print(f"   📝 Description: {component['description']}")
        
        # Show capabilities
        if component.get('capabilities'):
            print("🛠️ Capabilities:")
            for capability in component['capabilities']:
                print(f"   • {capability}")
        
        # Show usage examples
        if component.get('usage_examples'):
            print("💡 Usage examples:")
            for example in component['usage_examples']:
                print(f"   • {example}")
        
        # Show dependencies
        if component.get('dependencies'):
            print("🔗 Dependencies:")
            for dep in component['dependencies']:
                print(f"   • {dep}")
        
        # Show API methods if available
        if component.get('api_methods') and getattr(args, 'verbose', False):
            print("🔌 API methods:")
            for method in component['api_methods']:
                print(f"   • {method.get('name', 'unknown')}: {method.get('description', 'No description')}")
        
        # Show recent performance if available
        if component.get('performance_metrics'):
            metrics = component['performance_metrics']
            print("📈 Performance metrics:")
            print(f"   • Response time: {metrics.get('avg_response_time', 'unknown')}")
            print(f"   • Success rate: {metrics.get('success_rate', 'unknown')}")
            print(f"   • Error rate: {metrics.get('error_rate', 'unknown')}")
        
    except Exception as e:
        handle_cli_error(e, "Explain component", getattr(args, 'verbose', False))


def handle_demo_command(args):
    """Handle demo component command"""
    try:
        from empirica.bootstraps.extended_metacognitive_bootstrap import ExtendedMetacognitiveBootstrap
        
        component_name = getattr(args, 'component', 'random')
        print(f"🎭 Running demo for component: {component_name}")
        
        # Get component registry
        registry = get_component_registry()
        
        if component_name == 'random':
            # Pick a random working component
            components = registry.get_working_components()
            if not components:
                print("❌ No working components available for demo")
                return
            
            import random
            component = random.choice(components)
            component_name = component['name']
            print(f"🎲 Randomly selected: {component_name}")
        else:
            component = registry.get_component(component_name)
            if not component:
                print(f"❌ Component '{component_name}' not found")
                return
        
        # Run component demo
        demo_result = registry.run_component_demo(
            component_name,
            interactive=getattr(args, 'interactive', False),
            verbose=getattr(args, 'verbose', False)
        )
        
        print(f"✅ Demo complete for {component_name}")
        print(f"   🎯 Demo type: {demo_result.get('demo_type', 'standard')}")
        print(f"   ⏱️ Duration: {demo_result.get('duration', 'unknown')}")
        print(f"   📊 Result: {demo_result.get('result', 'unknown')}")
        
        # Show demo output
        if demo_result.get('output'):
            print("📄 Demo output:")
            print(demo_result['output'])
        
        # Show demo steps if verbose
        if getattr(args, 'verbose', False) and demo_result.get('steps'):
            print("🔍 Demo steps:")
            for i, step in enumerate(demo_result['steps'], 1):
                print(f"   {i}. {step.get('description', 'Unknown step')}")
                if step.get('result'):
                    print(f"      Result: {step['result']}")
        
        # Show next steps or related demos
        if demo_result.get('next_steps'):
            print("➡️ Next steps:")
            for step in demo_result['next_steps']:
                print(f"   • {step}")
        
        if demo_result.get('related_demos'):
            print("🔗 Related demos:")
            for related in demo_result['related_demos']:
                print(f"   • {related}")
        
    except Exception as e:
        handle_cli_error(e, "Component demo", getattr(args, 'verbose', False))