{
  inputs = {
    nixpkgs.url = "github:Nixos/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          nativeBuildInputs = [ 
            pkgs.uv 
            pkgs.python312
            pkgs.nodejs_22
            pkgs.awscli2
          ];

          UV_PYTHON_DOWNLOADS = "never";
        };
      });
    };
}