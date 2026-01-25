# Homebrew Formula for Empirica
# Documentation: https://docs.brew.sh/Formula-Cookbook
#
# This is the packaging template. The actual formula is in:
#   https://github.com/Nubaeon/homebrew-tap/blob/main/empirica.rb
#
# Installation:
#   brew tap nubaeon/tap
#   brew install empirica

class Empirica < Formula
  include Language::Python::Virtualenv

  desc "Epistemic self-assessment framework for AI agents"
  homepage "https://github.com/Nubaeon/empirica"
  url "https://files.pythonhosted.org/packages/source/e/empirica/empirica-1.4.2.tar.gz"
  sha256 "d42023e8284d35aa7aeba58a16cc3e62a83fd78348e6e5ce4e09b1e89f190d15"
  license "MIT"

  depends_on "python@3.11"

  # Let pip handle dependencies from pyproject.toml
  # No explicit resources needed - virtualenv_install_with_resources handles this

  def install
    virtualenv_install_with_resources
  end

  test do
    # Test that the CLI works
    assert_match "1.4.2", shell_output("#{bin}/empirica --version")

    # Test that key commands exist
    system "#{bin}/empirica", "session-create", "--help"
    system "#{bin}/empirica", "project-bootstrap", "--help"

    # Test Python import
    system Formula["python@3.11"].opt_bin/"python3", "-c", "from empirica.cli.cli_core import main"
  end
end
