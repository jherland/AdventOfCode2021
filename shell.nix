{
  pkgs ? import (builtins.fetchGit {
    url = "https://github.com/NixOS/nixpkgs/";
    ref = "nixos-21.05";
  }) {}
}:

pkgs.mkShell {
  name = "AoC21";
  buildInputs = with pkgs; [
    gitAndTools.gitFull
    pypy3
    python310
    python310Packages.venvShellHook
  ];
  venvDir = "./.venv";
  postShellHook = ''
    unset SOURCE_DATE_EPOCH
    pip install -r requirements.txt
  '';
}
