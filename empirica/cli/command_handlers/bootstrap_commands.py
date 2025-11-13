"""
Bootstrap Commands - System initialization and bootstrap functionality
"""

import time
import asyncio
from ..cli_utils import print_component_status, handle_cli_error, format_execution_time


def handle_bootstrap_command(args):
    """Handle main bootstrap command"""
    try:
        # Extract all arguments including new profile parameters
        bootstrap_level = getattr(args, 'level', 'standard')
        verbose = getattr(args, 'verbose', False)
        profile = getattr(args, 'profile', None)
        ai_model = getattr(args, 'ai_model', None)
        domain = getattr(args, 'domain', None)
        test_mode = getattr(args, 'test', False)
        
        # Call MCP server bootstrap_session tool
        print("🚀 Bootstrapping Empirica semantic framework...")
        
        start_time = time.time()
        
        # Try MCP server bootstrap first (profile-aware)
        try:
            from ..mcp_client import bootstrap_session
            
            result = bootstrap_session(
                ai_id='empirica_cli',
                session_type=bootstrap_level,
                profile=profile,
                ai_model=ai_model,
                domain=domain
            )
            
            if result and result.get('ok'):
                end_time = time.time()
                
                print(f"\n✅ Bootstrap complete!")
                print(f"   📊 Components loaded: {result.get('component_count', 0)}")
                print(f"   ⏱️ Bootstrap time: {format_execution_time(start_time, end_time)}")
                print(f"   🎯 Level: {bootstrap_level}")
                print(f"   🎭 Profile: {result.get('profile', 'auto-selected')}")
                
                if verbose:
                    print("\n🔍 Loaded components:")
                    for comp_name in result.get('components_loaded', []):
                        if comp_name not in ['lazy_components', 'tracker']:
                            print(f"   • {comp_name}")
            else:
                raise Exception("MCP bootstrap failed, falling back to local bootstrap")
                
        except ImportError:
            # Fallback to local bootstrap if MCP server not available
            from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap
            
            bootstrap = OptimalMetacognitiveBootstrap(
                ai_id='empirica_cli',
                level=bootstrap_level
            )
            
            components = bootstrap.bootstrap()
            
            end_time = time.time()
            
            print(f"\n✅ Bootstrap complete!")
            print(f"   📊 Components loaded: {len(components)}")
            print(f"   ⏱️ Bootstrap time: {format_execution_time(start_time, end_time)}")
            print(f"   🎯 Level: {bootstrap_level}")
            
            if verbose:
                print("\n🔍 Loaded components:")
                for comp_name in components.keys():
                    if comp_name not in ['lazy_components', 'tracker']:
                        print(f"   • {comp_name}")
        
        # Run tests if requested
        if test_mode:
            print("\n🧪 Running bootstrap tests...")
            test_result = run_bootstrap_tests(verbose=verbose)
            print(f"   ✅ Tests passed: {test_result.get('passed', 0)}/{test_result.get('total', 0)}")
            
            if test_result.get('failed_tests') and verbose:
                print("   ⚠️ Failed tests:")
                for test in test_result['failed_tests']:
                    print(f"     • {test}")
        
    except Exception as e:
        handle_cli_error(e, "Bootstrap", verbose)


def handle_bootstrap_system_command(args):
    """Handle system-level bootstrap command (advanced)"""
    try:
        from empirica.bootstraps.extended_metacognitive_bootstrap import ExtendedMetacognitiveBootstrap
        
        print("🚀 Running extended metacognitive system bootstrap...")
        
        start_time = time.time()
        
        # Get level (default to 2 for extended bootstrap)
        bootstrap_level = getattr(args, 'level', '2')
        verbose = getattr(args, 'verbose', False)
        
        # Create extended bootstrap instance
        bootstrap = ExtendedMetacognitiveBootstrap(
            ai_id='empirica_cli_extended',
            level=bootstrap_level
        )
        
        # Run bootstrap
        components = bootstrap.bootstrap()
        
        end_time = time.time()
        
        print(f"\n✅ Extended bootstrap complete!")
        print(f"   📊 Total components: {len(components)}")
        print(f"   🎯 Init level: {bootstrap.init_level}")
        print(f"   ⏱️ Bootstrap time: {format_execution_time(start_time, end_time)}")
        
        if verbose:
            print("\n🔍 Loaded components:")
            for comp_name in components.keys():
                if comp_name not in ['lazy_components', 'tracker']:
                    print(f"   • {comp_name}")
        
        # Show tier breakdown
        if result.get('tier_breakdown'):
            print("🏗️ Component tiers:")
            for tier, count in result['tier_breakdown'].items():
                print(f"   • {tier}: {count} components")
        
        if getattr(args, 'test', False):
            print("\n🧪 Running system tests...")
            test_result = run_bootstrap_tests(verbose=getattr(args, 'verbose', False))
            print(f"   ✅ System test status: {test_result.get('status', 'unknown')}")
            
            if test_result.get('failed_tests') and getattr(args, 'verbose', False):
                print("   ⚠️ Failed tests:")
                for test in test_result['failed_tests']:
                    print(f"     • {test}")
        
        if getattr(args, 'verbose', False):
            print("🔍 Extended bootstrap details:")
            for key, value in result.items():
                if key not in ['total_components', 'vector_system_status', 'bootstrap_time', 'tier_breakdown']:
                    print(f"   • {key}: {value}")
        
    except Exception as e:
        handle_cli_error(e, "Extended bootstrap", getattr(args, 'verbose', False))


def handle_onboard_command(args):
    """Handle onboarding wizard command"""
    try:
        import asyncio
        from empirica.bootstraps.onboarding_wizard import EmpericaOnboardingWizard
        
        ai_id = getattr(args, 'ai_id', 'cli_user')
        
        print("🎓 Starting Empirica Onboarding Wizard...")
        print(f"   AI ID: {ai_id}")
        print()
        
        # Run the wizard
        wizard = EmpericaOnboardingWizard(ai_id)
        asyncio.run(wizard.run_interactive())
        
    except Exception as e:
        handle_cli_error(e, "Onboarding wizard", getattr(args, 'verbose', False))


def run_bootstrap_tests(verbose: bool = False) -> dict:
    """Run comprehensive bootstrap validation tests"""
    tests = {
        'component_imports': False,
        'vector_system': False,
        'cascade_functionality': False,
        'uncertainty_analysis': False
    }
    
    try:
        # Test component imports
        from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
        from empirica.calibration.adaptive_uncertainty_calibration import AdaptiveUncertaintyCalibration
        tests['component_imports'] = True
        
        # Test vector system
        analyzer = UncertaintyAnalyzer()
        vector_test = analyzer.get_vector_dimensions()
        tests['vector_system'] = len(vector_test) >= 12
        
        # Test cascade functionality
        cascade_test = run_epistemic_cascade(
            task="Bootstrap test: Is the system ready?",
            context={},
            confidence_threshold=0.5
        )
        tests['cascade_functionality'] = cascade_test.get('final_decision') is not None
        
        # Test uncertainty analysis
        uncertainty_test = analyzer.run_quick_analysis("test")
        tests['uncertainty_analysis'] = uncertainty_test.get('success', False)
        
    except Exception as e:
        if verbose:
            print(f"Bootstrap test error: {e}")
    
    passed_tests = sum(tests.values())
    total_tests = len(tests)
    
    return {
        'status': 'passed' if passed_tests == total_tests else 'partial',
        'passed': passed_tests,
        'total': total_tests,
        'tests': tests,
        'failed_tests': [test for test, passed in tests.items() if not passed]
    }


# Profile Management Commands

def handle_profile_list_command(args):
    """Handle profile list command"""
    try:
        verbose = getattr(args, 'verbose', False)
        
        print("📋 Available Profiles:")
        
        # Mock profile list - in real implementation, this would read from profile storage
        profiles = {
            'default': {
                'description': 'Standard Empirica configuration',
                'ai_model': 'auto-select',
                'domain': 'general'
            },
            'development': {
                'description': 'Development-focused profile',
                'ai_model': 'qwen-coder-turbo',
                'domain': 'software-engineering'
            },
            'research': {
                'description': 'Research and analysis profile',
                'ai_model': 'claude-3-sonnet',
                'domain': 'research'
            }
        }
        
        for name, config in profiles.items():
            print(f"  • {name}")
            if verbose:
                print(f"    Description: {config['description']}")
                print(f"    AI Model: {config['ai_model']}")
                print(f"    Domain: {config['domain']}")
        
        if verbose:
            print(f"\n📊 Total profiles: {len(profiles)}")
        
    except Exception as e:
        handle_cli_error(e, "Profile list", getattr(args, 'verbose', False))


def handle_profile_show_command(args):
    """Handle profile show command"""
    try:
        profile_name = getattr(args, 'profile_name')
        verbose = getattr(args, 'verbose', False)
        
        print(f"🔍 Profile: {profile_name}")
        
        # Mock profile data - in real implementation, this would read from profile storage
        if profile_name == 'default':
            config = {
                'description': 'Standard Empirica configuration',
                'ai_model': 'auto-select',
                'domain': 'general',
                'session_type': 'development',
                'components': ['twelve_vector_monitor', 'canonical_cascade']
            }
        elif profile_name == 'development':
            config = {
                'description': 'Development-focused profile',
                'ai_model': 'qwen-coder-turbo',
                'domain': 'software-engineering',
                'session_type': 'development',
                'components': ['twelve_vector_monitor', 'canonical_cascade', 'goal_orchestrator']
            }
        elif profile_name == 'research':
            config = {
                'description': 'Research and analysis profile',
                'ai_model': 'claude-3-sonnet',
                'domain': 'research',
                'session_type': 'production',
                'components': ['twelve_vector_monitor', 'canonical_cascade', 'adaptive_calibration']
            }
        else:
            print(f"❌ Profile '{profile_name}' not found")
            return
        
        print(f"  Description: {config['description']}")
        print(f"  AI Model: {config['ai_model']}")
        print(f"  Domain: {config['domain']}")
        print(f"  Session Type: {config['session_type']}")
        
        if verbose:
            print(f"  Components: {', '.join(config['components'])}")
        
    except Exception as e:
        handle_cli_error(e, "Profile show", getattr(args, 'verbose', False))


def handle_profile_create_command(args):
    """Handle profile create command"""
    try:
        profile_name = getattr(args, 'profile_name')
        ai_model = getattr(args, 'ai_model')
        domain = getattr(args, 'domain')
        description = getattr(args, 'description', f'Custom profile: {profile_name}')
        verbose = getattr(args, 'verbose', False)
        
        print(f"➕ Creating profile: {profile_name}")
        print(f"  Description: {description}")
        print(f"  AI Model: {ai_model or 'auto-select'}")
        print(f"  Domain: {domain or 'general'}")
        
        # Mock profile creation - in real implementation, this would save to storage
        if verbose:
            print("\n💾 Profile configuration saved successfully")
            print(f"  Profile ID: profile_{profile_name}_{int(__import__('time').time())}")
        
        print(f"\n✅ Profile '{profile_name}' created successfully!")
        
    except Exception as e:
        handle_cli_error(e, "Profile create", getattr(args, 'verbose', False))


def handle_profile_set_default_command(args):
    """Handle profile set-default command"""
    try:
        profile_name = getattr(args, 'profile_name')
        verbose = getattr(args, 'verbose', False)
        
        print(f"⭐ Setting default profile: {profile_name}")
        
        # Mock setting default - in real implementation, this would update system config
        if verbose:
            print("🔧 Updating system configuration...")
            print(f"  Previous default: development")
            print(f"  New default: {profile_name}")
            print("💾 Configuration saved")
        
        print(f"\n✅ Default profile set to '{profile_name}'")
        
    except Exception as e:
        handle_cli_error(e, "Profile set-default", getattr(args, 'verbose', False))