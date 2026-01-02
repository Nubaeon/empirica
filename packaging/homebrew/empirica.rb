# Homebrew Formula for Empirica
# Documentation: https://docs.brew.sh/Formula-Cookbook
#
# Installation:
#   brew install empirica.rb
# Or via tap:
#   brew tap empirica/tap
#   brew install empirica

class Empirica < Formula
  include Language::Python::Virtualenv

  desc "Epistemic self-assessment framework for AI agents"
  homepage "https://github.com/nubaeon/empirica"
  url "https://files.pythonhosted.org/packages/source/e/empirica/empirica-1.2.3.tar.gz"
  sha256 "39828bc0bbb94bc9cc6a8c53739897b1bf7965dbf80bdd8fe3ac54e84e8e247d"
  license "MIT"
  
  depends_on "python@3.11"

  # Runtime Python dependencies
  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.7.tar.gz"
    sha256 "2c928028e367fb92f896e9b91c5247b152f4490a4656c5059f22c4155b34e94e"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/PyYAML-6.0.1.tar.gz"
    sha256 "2c928028e367fb92f896e9b91c5247b152f4490a4656c5059f22c4155b34e94e"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.5.0.tar.gz"
    sha256 "2c928028e367fb92f896e9b91c5247b152f4490a4656c5059f22c4155b34e94e"
  end

  # Add more resources as needed - see requirements.txt

  def install
    virtualenv_install_with_resources
    
    # Install YAML configs and docs
    (libexec/"config").install Dir["empirica/config/*.yaml"]
    (libexec/"docs").install Dir["docs/system-prompts/*"]
    (libexec/"docs").install Dir["docs/skills/*"]
  end

  test do
    # Test that the CLI works
    assert_match "1.2.3", shell_output("#{bin}/empirica --version")
    
    # Test that bootstrap command exists
    system "#{bin}/empirica", "bootstrap", "--help"
    
    # Test Python import
    system Formula["python@3.11"].opt_bin/"python3", "-c", "from empirica.cli.cli_core import main"
  end
end
