# ═══════════════════════════════════════════════════════════════
#  core/errors.py — Traduz os erros do yt-dlp para o que a pessoa entende
#
#  O yt-dlp devolve textos técnicos em inglês ("Sign in to confirm you're
#  not a bot", "HTTP Error 429"...). Aqui cada um vira: o que aconteceu,
#  por que costuma acontecer e o que tentar.
# ═══════════════════════════════════════════════════════════════
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    key: str            # identificador estável (usado nos testes)
    title: str          # frase curta: o que aconteceu
    message: str        # por que costuma acontecer
    tips: tuple         # o que tentar, em ordem


_UPDATE_TIP = "Atualize o Kyra Tube: cada versão nova traz o yt-dlp mais recente, e o YouTube muda sempre"
_RETRY_TIP = "Espere alguns minutos e tente de novo"

# (chave, padrão no texto do erro em minúsculas, título, mensagem, dicas) — a primeira que casar vale.
_RULES = [
    ("bot_check", r"confirm you.{0,3}re not a bot|sign in to confirm(?! your age)",
     "O YouTube pediu para confirmar que você não é um robô",
     "Isso acontece quando o YouTube bloqueia a sua conexão por um tempo: muitos acessos seguidos, IP "
     "compartilhado (rede de faculdade, empresa, VPN) ou um bloqueio momentâneo do provedor.",
     ("Reinicie o roteador (ou o Wi-Fi) para trocar o seu IP e tente de novo",
      "Se puder, teste em outra rede, como o 4G do celular",
      "Desligue VPN ou proxy, se estiver usando",
      _RETRY_TIP,
      _UPDATE_TIP)),
    ("rate_limit", r"http error 429|too many requests|rate.?limit",
     "Muitos pedidos em pouco tempo",
     "O YouTube limitou temporariamente a sua conexão porque houve acessos demais num intervalo curto.",
     (_RETRY_TIP + " (de 10 a 30 minutos costuma resolver)",
      "Reinicie o roteador para trocar o seu IP",
      "Baixe menos vídeos de uma vez")),
    ("forbidden", r"http error 403|forbidden",
     "O YouTube recusou o download deste vídeo",
     "O endereço do arquivo foi bloqueado ou expirou. Costuma ser um bloqueio momentâneo da sua conexão ou "
     "uma mudança do YouTube que ainda não está nesta versão.",
     ("Tente de novo em alguns minutos",
      "Reinicie o roteador para trocar o seu IP",
      _UPDATE_TIP)),
    ("private", r"private video|this video is private",
     "Este vídeo é privado",
     "Só quem o dono liberou consegue assistir, então não dá para baixar.",
     ("Peça ao dono do vídeo para torná-lo público ou não listado",)),
    ("members", r"members.?only|join this channel|available to this channel.s members",
     "Este vídeo é só para membros do canal",
     "O dono liberou o vídeo apenas para quem assina o canal.",
     ("Não dá para baixar sem ser membro do canal",)),
    ("age", r"confirm your age|age.?restricted|inappropriate for some users",
     "Este vídeo tem restrição de idade",
     "O YouTube só mostra esse vídeo para quem está logado em uma conta com idade confirmada, e o Kyra Tube "
     "não usa a sua conta.",
     ("Não dá para baixar vídeos com restrição de idade sem entrar numa conta",)),
    ("copyright", r"copyright|blocked it on|who has blocked it",
     "Este vídeo foi bloqueado por direitos autorais",
     "O dono ou uma gravadora bloqueou o vídeo, às vezes só em alguns países.",
     ("Procure outra versão do mesmo vídeo",
      "Se o bloqueio for só no seu país, um outro endereço de rede pode funcionar")),
    ("geo", r"available in your country|blocked in your country|geo.?restrict|your location",
     "Este vídeo não está disponível no seu país",
     "O dono limitou o vídeo a certas regiões.",
     ("Procure outra versão do mesmo vídeo",)),
    ("upcoming", r"premieres in|live event will begin|this live event|will begin in",
     "Este vídeo ainda não começou",
     "É uma estreia ou uma transmissão ao vivo agendada, e o arquivo só existe depois que ela acontece.",
     ("Tente de novo depois do horário marcado",)),
    ("unavailable", r"video unavailable|this video is unavailable|has been removed|no longer available|"
                    r"does not exist|account associated with this video has been terminated|http error 404",
     "Este vídeo não está disponível",
     "Ele foi removido, o canal foi apagado ou o endereço está errado.",
     ("Confira se o link está completo e abre no navegador",
      "Se abre no navegador mas não aqui, atualize o Kyra Tube e tente de novo")),
    ("bad_url", r"unsupported url|is not a valid url|no suitable|unable to extract|incomplete.{0,10}url",
     "Este link não parece ser de um vídeo",
     "O endereço não é de um vídeo ou playlist do YouTube que o app reconheça.",
     ("Copie o link direto da barra de endereços do navegador, com o https://",
      "Se for um link de compartilhar, cole o endereço completo")),
    ("network", r"getaddrinfo|network is unreachable|timed out|timeout|connection (?:reset|refused|aborted|error)|"
                r"urlopen error|name or service not known|temporary failure|unable to download webpage|"
                r"remote end closed|ssl|certificate",
     "Sem conexão com o YouTube",
     "O app não conseguiu falar com o YouTube. Pode ser a internet caindo, um bloqueio da rede (faculdade, "
     "empresa) ou o roteador travado.",
     ("Confira se a internet está funcionando no navegador",
      "Reinicie o roteador (já resolveu muitos casos parecidos)",
      "Desligue VPN ou proxy, se estiver usando",
      "Se estiver numa rede de empresa ou faculdade, teste em outra rede")),
    ("format", r"requested format is not available|no video formats|format.{0,20}not available",
     "Essa qualidade ou formato não existe para este vídeo",
     "Cada vídeo oferece uma lista diferente de qualidades.",
     ("Escolha \"Melhor\" na qualidade",
      "Tente outro formato, como MP4",
      _UPDATE_TIP)),
    ("ffmpeg", r"ffmpeg|ffprobe|postprocessing|post-processing|merge",
     "Não deu para juntar ou converter o arquivo",
     "A etapa final (juntar áudio e vídeo ou converter para MP3) falhou. Pode faltar espaço no disco, ou "
     "algum programa pode estar usando o arquivo.",
     ("Confira se há espaço livre no disco",
      "Feche players ou programas que possam estar usando o arquivo",
      "Tente de novo escolhendo outra pasta")),
    ("disk", r"no space left|errno 28|disk full|permission denied|errno 13|access is denied|"
             r"cannot create|read-only file system|the system cannot find the path",
     "Não deu para salvar o arquivo nessa pasta",
     "A pasta não existe mais, está cheia ou o Windows não deixa o app escrever nela.",
     ("Escolha outra pasta em \"Salvar em\" (por exemplo, Downloads)",
      "Confira se há espaço livre no disco")),
]


def explain(raw):
    """Texto de erro (do yt-dlp ou do sistema) → Problem com o que fazer."""
    text = (raw or "").lower()
    for key, pattern, title, message, tips in _RULES:
        if re.search(pattern, text):
            return Problem(key, title, message, tuple(tips))
    return Problem(
        "unknown",
        "Não deu para baixar este vídeo",
        "Aconteceu algo que o app não reconheceu. Quase sempre é uma mudança do YouTube ou uma falha "
        "passageira da conexão.",
        ("Tente de novo em alguns minutos",
         "Reinicie o roteador e tente outra vez",
         _UPDATE_TIP,
         "Se continuar, use \"Copiar detalhes\" e abra um aviso no GitHub do projeto"),
    )


def short_reason(raw, limit=300):
    """Primeira linha útil do erro técnico, sem o prefixo 'ERROR:' e sem códigos de cor."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", raw or "").strip()
    first = next((ln.strip() for ln in clean.splitlines() if ln.strip()), "")
    first = re.sub(r"^ERROR:\s*", "", first)
    return first[:limit]
