# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

source $(brew --prefix)/opt/powerlevel10k/powerlevel10k.zsh-theme
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh

[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

export PATH=$HOME:/usr/local/sbin:~/bin/:~/src/pulsara/devops/deployment/bin:/usr/local/opt/terraform@0.13/bin:$PATH

setopt HIST_IGNORE_DUPS
setopt APPENDHISTORY     #Append history to the history file (no overwriting)
# setopt SHAREHISTORY      #Share history across terminals
setopt INCAPPENDHISTORY  #Immediately append to the history file, not just when a term is killed
HISTFILE=~/.histfile
HISTSIZE=1000
SAVEHIST=1000

ZSH_AUTOSUGGEST_HISTORY_IGNORE=('cd *')

source ~/.alias

# asdf and SDK stuff
. /opt/homebrew/opt/asdf/libexec/asdf.sh

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
export HOMEBREW_GITHUB_API_TOKEN=$(cat ~/.github/pat)
alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'
