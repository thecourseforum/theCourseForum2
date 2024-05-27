local null_ls = require("null-ls")
local builtins = null_ls.builtins
local formatting = builtins.formatting

null_ls.setup({
	sources = {
		formatting.black.with({
			extra_args = { "-S", "--fast", "--line-length", "80" },
		}),
		formatting.isort.with({
			extra_args = { "--profile", "black", "--line-length", "80" },
		}),
		formatting.prettierd.with({
			env = {
				XDG_RUNTIME_DIR = vim.env.XDG_RUNTIME_DIR or (vim.env.XDG_DATA_HOME .. "/prettierd"),
			},
			filetypes = { "css", "javascript", "md" },
		}),
	},
})
