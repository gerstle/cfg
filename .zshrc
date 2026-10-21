# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Prompt, suggestions, and completion.
source ~/powerlevel10k/powerlevel10k.zsh-theme
source "${HOMEBREW_PREFIX:-$(brew --prefix)}/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
fpath=("${ASDF_DATA_DIR:-$HOME/.asdf}/completions" $fpath)
fpath+=("$HOME/.zfunc")

autoload -Uz compinit
compinit
zstyle ':completion:*' menu select

[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

# Search paths, preserving command precedence.
path=(
  "${KREW_ROOT:-$HOME/.krew}/bin"
  /opt/homebrew/opt/mysql-client/bin
  "${ASDF_DATA_DIR:-$HOME/.asdf}/shims"
  "${path[@]}"
)
### MANAGED BY RANCHER DESKTOP START (DO NOT EDIT)
export PATH="/Users/cgerstle/.rd/bin:$PATH"
### MANAGED BY RANCHER DESKTOP END (DO NOT EDIT)
export PATH="${HOME}/.local/bin:/usr/local/sbin:~/bin/:$PATH"

# Append history immediately; keep separate live histories in each terminal.
setopt HIST_IGNORE_DUPS APPENDHISTORY INCAPPENDHISTORY
HISTFILE=~/.histfile
HISTSIZE=1000
SAVEHIST=1000

ZSH_AUTOSUGGEST_HISTORY_IGNORE=('cd *')

source ~/.alias

# Use vim cli mode
bindkey -v
export KEYTIMEOUT=1

# home/end fixes for mac & iterm2
bindkey '^[[H' beginning-of-line
bindkey -M vicmd '^[[H' beginning-of-line
bindkey '^[[F' end-of-line
bindkey -M vicmd '^[[F' beginning-of-line

bindkey '^P' up-history
bindkey '^N' down-history

# backspace and ^h working even after
# returning from command mode
bindkey '^?' backward-delete-char
bindkey '^h' backward-delete-char

# ctrl-w removed word backwards
bindkey '^w' backward-kill-word

# ctrl-r starts searching history backward
bindkey '^r' history-incremental-search-backward

# shift-<direction> for moving up and down in command history when you have multi-line commands
bindkey -M vicmd 'K' up-history
bindkey -M vicmd 'J' up-history

test -e "${HOME}/.iterm2_shell_integration.zsh" && source "${HOME}/.iterm2_shell_integration.zsh"

export GREP_OPTIONS="--color=always"

# Default terminal editor and preferred full-screen editor for CLI tools.
export EDITOR=vim
export VISUAL="zed --wait"

# Discover kubeconfigs without walking the Kubernetes cache or including backups.
export KUBECONFIG="$(
  find "$HOME/.kube" -path "$HOME/.kube/cache" -prune -o \
    -type f -name 'config*' ! -path '*bak*' -print | tr '\n' ':'
)"

export ODA_IT_HOME='/Users/cgerstle/src/o/oda/oda-control-plane-app-it'
export OMNI_CURL_HOME='/Users/cgerstle/.local/bin'
export OMNI_CURL_ARGS='-a oci-security-token -p DEFAULT --tlsTrust /Users/cgerstle/.local/certs/tls-ca-bundle-pc-iad.pem -v'

# SDKMAN registers completions after compinit.
export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh"

# Set up fzf key bindings and fuzzy completion
_fzf_excludes='--exclude Library --exclude node_modules --exclude .terraform --exclude target --exclude build --exclude dist'
export FZF_DEFAULT_COMMAND="fd --type f --strip-cwd-prefix $_fzf_excludes; for dir in .config .local; do [ -d \"\$dir\" ] && fd --type f --hidden $_fzf_excludes . \"\$dir\"; done"
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND="fd --type d --strip-cwd-prefix $_fzf_excludes; for dir in .config .local; do [ -d \"\$dir\" ] && printf \"%s\\n\" \"\$dir\" && fd --type d --hidden $_fzf_excludes . \"\$dir\"; done"
unset _fzf_excludes
export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border --info=inline --cycle'
export FZF_CTRL_T_OPTS="--preview 'bat --style=numbers --color=always --line-range :200 {}'"
export FZF_ALT_C_OPTS="--preview 'ls -la {}'"
source <(fzf --zsh)
