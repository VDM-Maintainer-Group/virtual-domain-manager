#completion script for domain-manager

com_l1()
{
	local cur=${COMP_WORDS[COMP_CWORD]}
	COMPREPLY=( $(compgen -W "plugin" -- $cur) )
}

complete -F com_l1 domain-manager
