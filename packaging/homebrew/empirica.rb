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
  url "https://github.com/Nubaeon/empirica/releases/download/v1.0.1/empirica-1.0.1.tar.gz"
  sha256 "43e22ff9c6cdda053e7171b470445237981e00099e231410076d04f0483635f5"
  license "MIT"
  
  depends_on "python@3.11"

  # Runtime Python dependencies
  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.7.tar.gz"
    sha256 "ca9853ad459e787e2192211578cc907e7594e294c7ccc834310722b41b9ca6de"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/PyYAML-6.0.1.tar.gz"
    sha256 "bfdf460b1736c775f2ba9f6a92bca30bc2095067b8a9d77876d1fad6cc3b4a43"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.5.0.tar.gz"
    sha256 "0b8be5413c06aadfbe80e3ec8b2f32d9f94e2d6ce8a8f8e3f7d5a3c0b0e7f0a0"
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
    assert_match "1.0.0b0", shell_output("#{bin}/empirica --version")
    
    # Test that bootstrap command exists
    system "#{bin}/empirica", "bootstrap", "--help"
    
    # Test Python import
    system Formula["python@3.11"].opt_bin/"python3", "-c", "from empirica.cli.cli_core import main"
  end
end
