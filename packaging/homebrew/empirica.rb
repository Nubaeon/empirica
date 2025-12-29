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
  url "https://github.com/Nubaeon/empirica/releases/download/v1.1.1/empirica-1.1.1.tar.gz"
  sha256 "0126deaae3faecfefac32ec548f219fd349ec8366a660a10fdc3b776bf1170b3"
  license "MIT"
  
  depends_on "python@3.11"

  # Runtime Python dependencies
  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.7.tar.gz"
    sha256 "0126deaae3faecfefac32ec548f219fd349ec8366a660a10fdc3b776bf1170b3"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/PyYAML-6.0.1.tar.gz"
    sha256 "0126deaae3faecfefac32ec548f219fd349ec8366a660a10fdc3b776bf1170b3"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.5.0.tar.gz"
    sha256 "0126deaae3faecfefac32ec548f219fd349ec8366a660a10fdc3b776bf1170b3"
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
    assert_match "1.1.0", shell_output("#{bin}/empirica --version")
    
    # Test that bootstrap command exists
    system "#{bin}/empirica", "bootstrap", "--help"
    
    # Test Python import
    system Formula["python@3.11"].opt_bin/"python3", "-c", "from empirica.cli.cli_core import main"
  end
end
