# SPDX-License-Identifier: GPL-3.0-or-later
# Track Timer — billable work-time tracking for Blender.
# Copyright (C) 2026 oToddy.mp4
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
bl_info = {
    "name": "Track Timer",
    "author": "oToddy.mp4",
    "version": (1, 6, 2),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar (N) > Track Timer",
    "description": "Counts work time in Blender, pauses on lost focus and when idle, with parallel steps/milestones and automatic TXT report",
    "category": "3D View",
    "license": "GPL-3.0-or-later",
}

import bpy
import time
import os
import json
import uuid
import atexit
import platform
from datetime import datetime


# -------------------------------------------------------------------
# i18n — bundled translations (English US is the default)
# -------------------------------------------------------------------
# English lives in the code itself (every T() key IS the English
# text). Other languages are packaged below. Missing entries fall back
# to English automatically, so a partial translation can never break.

LANGUAGES = (
    ("en_US", "English (US)", ""),
    ("pt_BR", "Português (Brasil)", ""),
    ("es", "Español", ""),
    ("fr", "Français", ""),
)

# Addon id that also works packaged as a Blender 4.2+ extension
# (legacy single-file install: __package__ is empty, falls back to __name__).
_ADDON_ID = __package__ if __package__ else __name__

STRINGS = {
    "pt_BR": {
        "Start": "Iniciar",
        "Start / resume counting": "Inicia / continua a contagem",
        "Pause": "Pausar",
        "Pause counting (keeps the total)": "Pausa a contagem (mantém o total)",
        "Finish session": "Finalizar sessão",
        "Stop counting and log the session to the .csv/.json in the reports folder": "Para a contagem e registra a sessão no .csv/.json na pasta de relatórios",
        "Reset total": "Zerar total",
        "Reset total and session (to start a new model). Does NOT delete steps (use Clear steps for that)": "Zera o total e a sessão (para começar um modelo novo). NÃO apaga as etapas (use Limpar terminadas p/ isso)",
        "Adjust time": "Ajustar tempo",
        "Manual adjustment (e.g. forgot to start, or counted non-work time)": "Ajuste manual (ex: esqueceu de ligar, ou contou tempo que não era trabalho)",
        "Minutes (+/-)": "Minutos (+/-)",
        "Export CSV": "Exportar CSV",
        "Update the .tracktime.csv and .milestones.csv in the reports folder": "Atualiza o .tracktime.csv e o .milestones.csv na pasta de relatórios",
        "Generate report now": "Gerar relatório agora",
        "Generate the TXT report in the reports folder, with the content chosen on the settings page": "Gera o relatório TXT na pasta de relatórios, com o conteúdo escolhido na página de configuração",
        "Open reports folder": "Abrir pasta de relatórios",
        "Open the folder with the TXT report and CSVs": "Abre a pasta onde ficam o relatório TXT e os CSVs",
        "Add step": "Adicionar etapa",
        "Add a step (you can add before or during counting)": "Adiciona uma etapa (pode adicionar antes ou durante a contagem)",
        "Step name": "Nome da etapa",
        "Start now": "Já começar agora",
        "If on, the step is born marked as 'in progress' (you can mark several at the same time)": "Se ligado, a etapa já nasce marcada como 'em andamento' (pode marcar várias ao mesmo tempo)",
        "Remove step": "Remover etapa",
        "Remove the selected step": "Remove a etapa selecionada",
        "Start / Pause step": "Começar / Pausar etapa",
        "Mark/unmark 'I'm working on this right now'. You can keep SEVERAL active at the same time. If the global timer is stopped, it starts by itself": "Marca/desmarca 'estou trabalhando nisto agora'. Pode deixar VÁRIAS ativas ao mesmo tempo. Se o timer global estiver parado, ele inicia sozinho",
        "Done! / Reopen": "Terminei! / Reabrir",
        "Mark the step as DONE (freezes its time) or reopen a finished step": "Marca a etapa como TERMINADA (congela o tempo) ou reabre uma etapa terminada",
        "Move step": "Mover etapa",
        "Move the step up/down in the list": "Sobe/desce a etapa na lista",
        "Clear finished": "Limpar terminadas",
        "Remove all finished steps from the list (keeps the open ones)": "Remove da lista todas as etapas já terminadas (mantém as em aberto)",
        "Load example outline": "Criar roteiro exemplo",
        "Add example steps (Blocking, Modeling, UV, Texturing...) — skips ones that already exist": "Adiciona etapas de exemplo (Blocagem, Modelagem, UV, Textura...) — pula as que já existem",
        "Adjust step": "Ajustar etapa",
        "Manual time adjustment of the selected step": "Ajuste manual do tempo da etapa selecionada",
        "Counting": "Contando",
        "Total (s)": "Total (s)",
        "Session (s)": "Sessão (s)",
        "Pause reason": "Motivo pausa",
        "Pause when Blender loses focus": "Pausar quando o Blender perde o foco",
        "If on: minimized, switched window/app or watching a video = pause. If off: it counts straight until you pause/finish": "Se ligado: minimizou, trocou de janela/app ou foi ver vídeo = pausa. Se desligado: conta direto até você pausar/finalizar",
        "Pause when idle": "Pausar quando ocioso",
        "Pauses even with Blender in front if there is no keyboard/mouse for X minutes (coffee break). Windows only.": "Pausa mesmo com o Blender na frente, se não houver teclado/mouse por X minutos (ir tomar café). Windows apenas.",
        "Idle (min)": "Ociosidade (min)",
        "Minutes without keyboard/mouse to count as idle": "Minutos sem teclado/mouse para considerar ocioso",
        "Rate / hour": "Valor/hora",
        "Optional: to estimate the job value": "Opcional: para estimar o valor do trabalho",
        "Show in status bar": "Mostrar na barra de status",
        "Auto backup next to the .blend": "Backup automático ao lado do .blend",
        "Saves .tracktime.json next to the .blend every 30s and on finish, so no time is lost if you close without saving": "Salva .tracktime.json ao lado do .blend a cada 30s e ao finalizar, para não perder tempo se fechar sem salvar",
        "Selected step": "Etapa selecionada",
        "Session started at": "Sessão iniciada em",
        "Time the current session started (used in the report)": "Hora em que a sessão atual começou (usada no relatório)",
        "Project started at": "Projeto iniciado em",
        "Time work on this file started (used in the report)": "Hora em que o trabalho neste arquivo começou (usada no relatório)",
        "Last report": "Último relatório",
        "Path of the last generated TXT report": "Caminho do último relatório TXT gerado",
        "Step": "Etapa",
        "ID": "ID",
        "Stable step identity (internal: protects time against Ctrl+Z)": "Identidade estável da etapa (uso interno: protege o tempo contra Ctrl+Z)",
        "In progress": "Em andamento",
        "Marked = you are working on THIS step right now. You can mark several at the same time": "Marcada = você está trabalhando NESTA etapa agora. Pode marcar várias ao mesmo tempo",
        "Done": "Terminada",
        "Marked = finished step, frozen time": "Marcada = etapa concluída, tempo congelado",
        "Seconds": "Segundos",
        "Created at": "Criada em",
        "Finished at": "Terminada em",
        "Header (project, folder, date)": "Cabeçalho (projeto, pasta, data)",
        "Hours spent (total)": "Horas gastas (total)",
        "Current session hours": "Horas da sessão atual",
        "Period (start-end time)": "Período (hora início-fim)",
        "Shows project start, session start and end": "Mostra início do projeto, início e fim da sessão",
        "Estimated value": "Valor estimado",
        "Steps table": "Tabela de etapas",
        "Lists each step with status, time, start and end": "Lista cada etapa com status, tempo, início e fim",
        "Sessions history": "Histórico de sessões",
        "Settings used": "Configuração usada",
        "Generate/update on save and session finish": "Gerar/atualizar ao salvar e ao finalizar sessão",
        "Updates the TXT in the reports folder whenever you save the .blend or finish a session": "Atualiza o TXT na pasta de relatórios sempre que você salvar o .blend ou finalizar uma sessão",
        "Generate when Blender closes": "Gerar ao fechar o Blender",
        "Tries to update the TXT when quitting Blender (via exit auto-save)": "Tenta atualizar o TXT ao sair do Blender (via salvamento automático de saída)",
        "File suffix": "Sufixo do arquivo",
        "E.g. _REPORT creates 'mymodel_REPORT.txt' in the reports folder": "Ex: _RELATORIO gera 'meumodelo_RELATORIO.txt' na pasta de relatórios",
        "Language": "Idioma",
        "Reports folder name": "Nome da pasta de relatórios",
        "Folder created next to the .blend to hold the TXT report and CSVs": "Pasta criada ao lado do .blend para guardar o relatório TXT e os CSVs",
        "What goes into the TXT report ({folder}):": "O que entra no relatório TXT ({folder}):",
        "Automatic:": "Automático:",
        "COUNTING...": "CONTANDO...",
        "STOPPED": "PARADO",
        "PAUSED — Blender unfocused": "PAUSADO — Blender sem foco",
        "PAUSED — idle for {m}min": "PAUSADO — ocioso há {m}min",
        "Total: {t}": "Total: {t}",
        "Session: {t}": "Sessão: {t}",
        "Est. value:": "Valor est.:",
        "currency_symbol": "R$",
        "Steps  •  {a} in progress  •  {d}/{n} done": "Etapas  •  {a} em andamento  •  {d}/{n} prontas",
        "Selected: {n} — {t}": "Selecionada: {n} — {t}",
        "  [DONE]": "  [TERMINADA]",
        "  [WORKING NOW]": "  [FAZENDO AGORA]",
        "Pause step": "Pausar etapa",
        "Start step": "Começar etapa",
        "Reopen": "Reabrir",
        "DONE!": "TERMINEI!",
        "No steps. Add BLOCKING, etc.": "Nenhuma etapa. Adicione BLOCAGEM, etc.",
        "Global timer stopped: active steps don't count.": "Timer global parado: etapas ativas não contam.",
        "TXT report (reports folder)": "Relatório TXT (pasta de relatórios)",
        "Last: {f}": "Último: {f}",
        "Content in Preferences > Add-ons > Track Timer": "Conteúdo em Preferences > Add-ons > Track Timer",
        "Focus/idle auto: Windows only.": "Foco/ociosidade auto: Windows apenas.",
        "On Linux/Mac it counts straight.": "No Linux/Mac conta direto.",
        "Save the .blend to enable .json/.csv backup": "Salve o .blend p/ ativar backup .json/.csv",
        "{n} steps": "{n} etapas",
        "BLOCKING": "BLOCAGEM",
        "DETAILED MODELING": "MODELAGEM DETALHADA",
        "RETOPOLOGY": "RETOPOLOGIA",
        "TEXTURING": "TEXTURA",
        "LIGHTING": "ILUMINAÇÃO",
        "POST / DELIVERY": "PÓS / ENTREGA",
        "Step {n}": "Etapa {n}",
        "Track Timer: counting started": "Track Timer: contagem iniciada",
        "Track Timer: paused": "Track Timer: pausado",
        "Track Timer: session of {s} logged. Total: {t}": "Track Timer: sessão de {s} registrada. Total: {t}",
        "Track Timer: total reset (steps kept)": "Track Timer: total zerado (etapas mantidas)",
        "Track Timer: total adjusted to {t}": "Track Timer: total ajustado para {t}",
        "Track Timer: CSVs updated in the reports folder": "Track Timer: CSVs atualizados na pasta de relatórios",
        "Save the .blend first (reports live in its folder)": "Salve o .blend primeiro (os relatórios ficam na pasta dele)",
        "Step '{n}' added": "Etapa '{n}' adicionada",
        "Step '{n}' removed": "Etapa '{n}' removida",
        "No step selected": "Nenhuma etapa selecionada",
        "'{n}' already finished — reopen it to continue": "'{n}' já terminada — reabra antes de continuar",
        "'{n}' in progress (timer started)": "'{n}' em andamento (timer iniciado)",
        "'{n}' in progress": "'{n}' em andamento",
        "'{n}' paused (kept time: {t})": "'{n}' pausada (tempo mantido: {t})",
        "'{n}' DONE in {t}": "'{n}' TERMINADA em {t}",
        "'{n}' reopened": "'{n}' reaberta",
        "'{n}' adjusted to {t}": "'{n}' ajustada para {t}",
        "{n} example steps added": "{n} etapas de exemplo adicionadas",
        "Outline already exists": "Roteiro já existe",
        "Report saved: {p}": "Relatório salvo: {p}",
        "Could not generate the report": "Não foi possível gerar o relatório",
        "Save the .blend first (the report lives in its folder)": "Salve o .blend primeiro (o relatório fica na pasta dele)",
        "Folder: {f}": "Pasta: {f}",
        "TIME REPORT — TRACK TIMER": "RELATÓRIO DE HORAS — TRACK TIMER",
        "Project   :": "Projeto   :",
        "Folder    :": "Pasta     :",
        "Generated :": "Gerado em :",
        "(reason: {r})": "(motivo: {r})",
        "manual": "manual",
        "save": "salvamento",
        "session finished": "sessão finalizada",
        "project switch": "troca de projeto",
        "exit": "saída",
        "PERIOD (start-end time)": "PERÍODO (hora início-fim)",
        "Project start :": "Início do projeto :",
        "Session start :": "Início da sessão   :",
        "Session end   :": "Fim da sessão     :",
        "(in progress)": "(em andamento)",
        "Current session : none (click Start)": "Sessão atual        : nenhuma (clique em Iniciar)",
        "HOURS SPENT": "HORAS GASTAS",
        "Total   :": "Total   :",
        "Session :": "Sessão  :",
        "VALUE": "VALOR",
        "Rate/hour     :": "Valor/hora     :",
        "Estimated value :": "Valor estimado :",
        "STEPS": "ETAPAS",
        "(no steps created)": "(nenhuma etapa criada)",
        "DONE": "TERMINADA",
        "IN PROGRESS": "EM ANDAMENTO",
        "PAUSED": "PAUSADA",
        "PENDING": "PENDENTE",
        "start:": "início:",
        "end:": "fim:",
        "now (in progress)": "agora (em andamento)",
        "Summary: {d}/{n} done": "Resumo: {d}/{n} terminadas",
        "SESSIONS HISTORY": "HISTÓRICO DE SESSÕES",
        "(no finished sessions logged)": "(nenhuma sessão finalizada registrada)",
        "session": "sessão",
        "total": "total",
        "SETTINGS USED": "CONFIGURAÇÃO USADA",
        "Pause when unfocused :": "Pausar sem foco :",
        "Pause when idle     :": "Pausar ocioso   :",
        "YES": "SIM",
        "NO": "NÃO",
        "({m} min)": "({m} min)",
        "Generated by the Track Timer addon": "Gerado pelo addon Track Timer",
        "Render: {t}": "Render: {t}",
        "(recovered)": "(recuperada)",
        "Allowed apps (e.g. PureRef, Photoshop)": "Apps permitidos (ex: PureRef, Photoshop)",
        "Comma-separated names. When one of these apps is focused, it still counts as work": "Nomes separados por vírgula. Quando um desses apps está em foco, continua contando como trabalho",
        "Focus grace (s)": "Tolerância de foco (s)",
        "Seconds of lost focus tolerated before pausing (quick Alt+Tab)": "Segundos de perda de foco tolerados antes de pausar (Alt+Tab rápido)",
        "Step time mode": "Modo de tempo das etapas",
        "How time is shared when several steps are active at once": "Como o tempo é dividido quando várias etapas estão ativas",
        "Count in parallel": "Contar em paralelo",
        "Split between active steps": "Dividir entre etapas ativas",
        "Currency symbol": "Símbolo da moeda",
        "Optional symbol (empty = automatic per language)": "Símbolo opcional (vazio = automático por idioma)",
        "Tip: install xdotool and xprintidle for focus + idle detection": "Dica: instale xdotool e xprintidle para detecção de foco + ociosidade",
        "Print / Save as PDF": "Imprimir / Salvar em PDF",
        "Project:": "Projeto:",
        "Client:": "Cliente:",
        "Status": "Status",
        "Time": "Tempo",
        "Start time": "Início",
        "End": "Fim",
        "Session": "Sessão",
        "Total": "Total",
        "General": "Geral",
        "Animation": "Animação",
        "Archviz": "Archviz",
        "Motion": "Motion",
        "Extras:": "Extras:",
        "Example outline": "Roteiro exemplo",
        "REFERENCES": "REFERÊNCIAS",
        "SPLINE": "SPLINE",
        "POLISH": "REFINO",
        "PLAYBLAST": "PLAYBLAST",
        "FINAL RENDER": "RENDER FINAL",
        "DELIVERY": "ENTREGA",
        "MODELING": "MODELAGEM",
        "MATERIALS": "MATERIAIS",
        "STORYBOARD": "STORYBOARD",
        "STYLEFRAMES": "STYLEFRAMES",
        "ANIMATION": "ANIMAÇÃO",
        "COMPOSITING": "COMPOSIÇÃO",
        "Generate HTML report": "Gerar relatório HTML",
        "Generate a printable HTML report (open in a browser, print to PDF)": "Gera um relatório HTML imprimível (abra no navegador, imprima em PDF)",
        "Also generate HTML report": "Gerar relatório HTML junto",
        "Write a printable HTML version next to the TXT on every report": "Grava uma versão HTML imprimível junto do TXT a cada relatório",
        "Show timer overlay in viewport": "Mostrar relógio no viewport",
        "Always-visible clock in the 3D viewport (may cost redraws in heavy scenes)": "Relógio sempre visível no viewport 3D (pode custar redesenhos em cenas pesadas)",
        "Show today / week": "Mostrar hoje / semana",
        "Show today's and this week's hours in the panel": "Mostra as horas de hoje e da semana no painel",
        "Client name": "Nome do cliente",
        "Shown in the HTML report header": "Exibido no cabeçalho do relatório HTML",
        "Project name": "Nome do projeto",
        "Shown in the HTML report header (empty = .blend name)": "Exibido no cabeçalho do relatório HTML (vazio = nome do .blend)",
        "Today: {t}": "Hoje: {t}",
        "This week: {t}": "Semana: {t}",
        "Render": "Render",
        "Folder:": "Pasta:",
        "Generated:": "Gerado em:",
        "Allow app": "Permitir app",
        "Add this app to the allowed list (counts as work when focused)": "Adiciona este app à lista de permitidos (conta como trabalho em foco)",
        "Remove app": "Remover app",
        "Remove this app from the allowed list": "Remove este app da lista de permitidos",
        "Add focused app": "Adicionar app em foco",
        "Add the last app seen in focus (switch to it first if the list is empty)": "Adiciona o último app visto em foco (alterne para ele antes se a lista estiver vazia)",
        "No other app seen yet — switch to it first": "Nenhum outro app visto ainda — alterne para ele antes",
        "'{n}' will now count as work": "'{n}' agora conta como trabalho",
        "'{n}' removed from allowed": "'{n}' removido dos permitidos",
        "Work apps (counted as work even when focused):": "Apps de trabalho (contam mesmo em foco):",
        "(none — only Blender counts)": "(nenhum — só o Blender conta)",
        "Type to filter:": "Digite para filtrar:",
        "Add \"{x}\"": "Adicionar \"{x}\"",
        "Focused: {x}": "Em foco: {x}",
        "Blender (this window)": "Blender (esta janela)",
        "unknown": "desconhecido",
        "Preferences unavailable": "Preferências indisponíveis",
        "Client": "Cliente",
        "Project": "Projeto",
        "Client / Project": "Cliente / Projeto",
        "Show client header": "Mostrar cabeçalho de cliente",
        "Show the client/project fields at the top of the panel (fill in first)": "Mostra os campos cliente/projeto no topo do painel (preencha primeiro)",
        "Step auto-start": "Auto-início das etapas",
        "Automatically start step 1 on new outlines and advance to the next step on finish": "Inicia a etapa 1 em roteiros novos e avança para a próxima ao terminar",
        "Avg session": "Sessão média",
        "avg of {n} sessions": "média de {n} sessões",
        "Average session": "Sessão média",
        "Show the average session time in the report (from all logged sessions)": "Mostra o tempo médio por sessão no relatório (de todas as sessões registradas)",
        "Client    :": "Cliente   :",
        "Start on first edit or save": "Iniciar no primeiro uso (editar ou salvar)",
        "Start counting on the first scene change or save while everything is still zeroed, so no work goes untracked": "Inicia a contagem na primeira alteração da cena ou ao salvar, com tudo ainda zerado, para nenhum trabalho ficar sem contar",
    },
    "es": {
        "Start": "Iniciar",
        "Start / resume counting": "Inicia / continúa el conteo",
        "Pause": "Pausar",
        "Pause counting (keeps the total)": "Pausa el conteo (mantiene el total)",
        "Finish session": "Finalizar sesión",
        "Stop counting and log the session to the .csv/.json in the reports folder": "Detiene el conteo y registra la sesión en el .csv/.json de la carpeta de informes",
        "Reset total": "Poner a cero",
        "Reset total and session (to start a new model). Does NOT delete steps (use Clear steps for that)": "Pone a cero el total y la sesión (para empezar un modelo nuevo). NO borra los pasos (usa Limpiar terminados)",
        "Adjust time": "Ajustar tiempo",
        "Manual adjustment (e.g. forgot to start, or counted non-work time)": "Ajuste manual (ej.: olvidaste iniciar, o contó tiempo que no era trabajo)",
        "Minutes (+/-)": "Minutos (+/-)",
        "Export CSV": "Exportar CSV",
        "Update the .tracktime.csv and .milestones.csv in the reports folder": "Actualiza el .tracktime.csv y el .milestones.csv en la carpeta de informes",
        "Generate report now": "Generar informe ahora",
        "Generate the TXT report in the reports folder, with the content chosen on the settings page": "Genera el informe TXT en la carpeta de informes, con el contenido elegido en la página de ajustes",
        "Open reports folder": "Abrir carpeta de informes",
        "Open the folder with the TXT report and CSVs": "Abre la carpeta con el informe TXT y los CSV",
        "Add step": "Añadir paso",
        "Add a step (you can add before or during counting)": "Añade un paso (puedes añadir antes o durante el conteo)",
        "Step name": "Nombre del paso",
        "Start now": "Empezar ahora",
        "If on, the step is born marked as 'in progress' (you can mark several at the same time)": "Si está activo, el paso nace marcado 'en curso' (puedes marcar varios a la vez)",
        "Remove step": "Quitar paso",
        "Remove the selected step": "Quita el paso seleccionado",
        "Start / Pause step": "Empezar / Pausar paso",
        "Mark/unmark 'I'm working on this right now'. You can keep SEVERAL active at the same time. If the global timer is stopped, it starts by itself": "Marca/desmarca 'estoy trabajando en esto ahora'. Puedes mantener VARIOS activos a la vez. Si el temporizador global está detenido, se inicia solo",
        "Done! / Reopen": "¡Listo! / Reabrir",
        "Mark the step as DONE (freezes its time) or reopen a finished step": "Marca el paso como LISTO (congela su tiempo) o reabre un paso terminado",
        "Move step": "Mover paso",
        "Move the step up/down in the list": "Sube/baja el paso en la lista",
        "Clear finished": "Limpiar terminados",
        "Remove all finished steps from the list (keeps the open ones)": "Quita de la lista todos los pasos terminados (conserva los abiertos)",
        "Load example outline": "Crear guía de ejemplo",
        "Add example steps (Blocking, Modeling, UV, Texturing...) — skips ones that already exist": "Añade pasos de ejemplo (Bloqueo, Modelado, UV, Texturas...) — omite los que ya existen",
        "Adjust step": "Ajustar paso",
        "Manual time adjustment of the selected step": "Ajuste manual del tiempo del paso seleccionado",
        "Counting": "Contando",
        "Total (s)": "Total (s)",
        "Session (s)": "Sesión (s)",
        "Pause reason": "Motivo de pausa",
        "Pause when Blender loses focus": "Pausar cuando Blender pierde el foco",
        "If on: minimized, switched window/app or watching a video = pause. If off: it counts straight until you pause/finish": "Si está activo: minimizado, otra ventana/app o ver un vídeo = pausa. Si no: cuenta seguido hasta pausar/finalizar",
        "Pause when idle": "Pausar si inactivo",
        "Pauses even with Blender in front if there is no keyboard/mouse for X minutes (coffee break). Windows only.": "Pausa aunque Blender esté al frente si no hay teclado/ratón durante X minutos (pausa café). Solo Windows.",
        "Idle (min)": "Inactividad (min)",
        "Minutes without keyboard/mouse to count as idle": "Minutos sin teclado/ratón para contar como inactivo",
        "Rate / hour": "Tarifa / hora",
        "Optional: to estimate the job value": "Opcional: para estimar el valor del trabajo",
        "Show in status bar": "Mostrar en la barra de estado",
        "Auto backup next to the .blend": "Copia auto junto al .blend",
        "Saves .tracktime.json next to the .blend every 30s and on finish, so no time is lost if you close without saving": "Guarda .tracktime.json junto al .blend cada 30 s y al finalizar, para no perder tiempo si cierras sin guardar",
        "Selected step": "Paso seleccionado",
        "Session started at": "Sesión iniciada",
        "Time the current session started (used in the report)": "Hora de inicio de la sesión actual (usada en el informe)",
        "Project started at": "Proyecto iniciado",
        "Time work on this file started (used in the report)": "Hora de inicio del trabajo en este archivo (usada en el informe)",
        "Last report": "Último informe",
        "Path of the last generated TXT report": "Ruta del último informe TXT generado",
        "Step": "Paso",
        "ID": "ID",
        "Stable step identity (internal: protects time against Ctrl+Z)": "Identidad estable del paso (interno: protege el tiempo contra Ctrl+Z)",
        "In progress": "En curso",
        "Marked = you are working on THIS step right now. You can mark several at the same time": "Marcado = estás trabajando en ESTE paso ahora. Puedes marcar varios a la vez",
        "Done": "Listo",
        "Marked = finished step, frozen time": "Marcado = paso terminado, tiempo congelado",
        "Seconds": "Segundos",
        "Created at": "Creado",
        "Finished at": "Terminado",
        "Header (project, folder, date)": "Encabezado (proyecto, carpeta, fecha)",
        "Hours spent (total)": "Horas (total)",
        "Current session hours": "Horas de la sesión actual",
        "Period (start-end time)": "Período (hora inicio-fin)",
        "Shows project start, session start and end": "Muestra inicio del proyecto, inicio y fin de la sesión",
        "Estimated value": "Valor estimado",
        "Steps table": "Tabla de pasos",
        "Lists each step with status, time, start and end": "Lista cada paso con estado, tiempo, inicio y fin",
        "Sessions history": "Historial de sesiones",
        "Settings used": "Ajustes usados",
        "Generate/update on save and session finish": "Generar/actualizar al guardar y al finalizar",
        "Updates the TXT in the reports folder whenever you save the .blend or finish a session": "Actualiza el TXT en la carpeta de informes al guardar el .blend o finalizar una sesión",
        "Generate when Blender closes": "Generar al cerrar Blender",
        "Tries to update the TXT when quitting Blender (via exit auto-save)": "Intenta actualizar el TXT al salir de Blender (autoguardado de salida)",
        "File suffix": "Sufijo de archivo",
        "E.g. _REPORT creates 'mymodel_REPORT.txt' in the reports folder": "Ej.: _INFORME crea 'mimodelo_INFORME.txt' en la carpeta de informes",
        "Language": "Idioma",
        "Reports folder name": "Nombre de la carpeta de informes",
        "Folder created next to the .blend to hold the TXT report and CSVs": "Carpeta creada junto al .blend para el informe TXT y los CSV",
        "What goes into the TXT report ({folder}):": "Contenido del informe TXT ({folder}):",
        "Automatic:": "Automático:",
        "COUNTING...": "CONTANDO...",
        "STOPPED": "DETENIDO",
        "PAUSED — Blender unfocused": "PAUSADO — Blender sin foco",
        "PAUSED — idle for {m}min": "PAUSADO — inactivo {m} min",
        "Total: {t}": "Total: {t}",
        "Session: {t}": "Sesión: {t}",
        "Est. value:": "Valor est.:",
        "currency_symbol": "€",
        "Steps  •  {a} in progress  •  {d}/{n} done": "Pasos  •  {a} en curso  •  {d}/{n} listos",
        "Selected: {n} — {t}": "Seleccionado: {n} — {t}",
        "  [DONE]": "  [LISTO]",
        "  [WORKING NOW]": "  [EN CURSO]",
        "Pause step": "Pausar paso",
        "Start step": "Empezar paso",
        "Reopen": "Reabrir",
        "DONE!": "¡LISTO!",
        "No steps. Add BLOCKING, etc.": "Sin pasos. Añade BLOCKING, etc.",
        "Global timer stopped: active steps don't count.": "Temporizador global detenido: los pasos activos no cuentan.",
        "TXT report (reports folder)": "Informe TXT (carpeta de informes)",
        "Last: {f}": "Último: {f}",
        "Content in Preferences > Add-ons > Track Timer": "Contenido en Preferences > Add-ons > Track Timer",
        "Focus/idle auto: Windows only.": "Foco/inactividad auto: solo Windows.",
        "On Linux/Mac it counts straight.": "En Linux/Mac cuenta seguido.",
        "Save the .blend to enable .json/.csv backup": "Guarda el .blend para activar la copia .json/.csv",
        "{n} steps": "{n} pasos",
        "BLOCKING": "BLOQUEO",
        "DETAILED MODELING": "MODELADO DETALLADO",
        "RETOPOLOGY": "RETOPOLOGÍA",
        "TEXTURING": "TEXTURAS",
        "LIGHTING": "ILUMINACIÓN",
        "POST / DELIVERY": "POST / ENTREGA",
        "Step {n}": "Paso {n}",
        "Track Timer: counting started": "Track Timer: conteo iniciado",
        "Track Timer: paused": "Track Timer: pausado",
        "Track Timer: session of {s} logged. Total: {t}": "Track Timer: sesión de {s} registrada. Total: {t}",
        "Track Timer: total reset (steps kept)": "Track Timer: total a cero (pasos conservados)",
        "Track Timer: total adjusted to {t}": "Track Timer: total ajustado a {t}",
        "Track Timer: CSVs updated in the reports folder": "Track Timer: CSV actualizados en la carpeta de informes",
        "Save the .blend first (reports live in its folder)": "Guarda el .blend primero (los informes van en su carpeta)",
        "Step '{n}' added": "Paso '{n}' añadido",
        "Step '{n}' removed": "Paso '{n}' quitado",
        "No step selected": "Ningún paso seleccionado",
        "'{n}' already finished — reopen it to continue": "'{n}' ya está listo — reábrelo para continuar",
        "'{n}' in progress (timer started)": "'{n}' en curso (temporizador iniciado)",
        "'{n}' in progress": "'{n}' en curso",
        "'{n}' paused (kept time: {t})": "'{n}' pausado (tiempo: {t})",
        "'{n}' DONE in {t}": "'{n}' LISTO en {t}",
        "'{n}' reopened": "'{n}' reabierto",
        "'{n}' adjusted to {t}": "'{n}' ajustado a {t}",
        "{n} example steps added": "{n} pasos de ejemplo añadidos",
        "Outline already exists": "La guía ya existe",
        "Report saved: {p}": "Informe guardado: {p}",
        "Could not generate the report": "No se pudo generar el informe",
        "Save the .blend first (the report lives in its folder)": "Guarda el .blend primero (el informe va en su carpeta)",
        "Folder: {f}": "Carpeta: {f}",
        "TIME REPORT — TRACK TIMER": "INFORME DE HORAS — TRACK TIMER",
        "Project   :": "Proyecto  :",
        "Folder    :": "Carpeta   :",
        "Generated :": "Generado  :",
        "(reason: {r})": "(motivo: {r})",
        "manual": "manual",
        "save": "guardado",
        "session finished": "sesión finalizada",
        "project switch": "cambio de proyecto",
        "exit": "salida",
        "PERIOD (start-end time)": "PERÍODO (hora inicio-fin)",
        "Project start :": "Inicio del proyecto :",
        "Session start :": "Inicio de la sesión :",
        "Session end   :": "Fin de la sesión    :",
        "(in progress)": "(en curso)",
        "Current session : none (click Start)": "Sesión actual       : ninguna (pulsa Iniciar)",
        "HOURS SPENT": "HORAS",
        "Total   :": "Total   :",
        "Session :": "Sesión  :",
        "VALUE": "VALOR",
        "Rate/hour     :": "Tarifa/hora    :",
        "Estimated value :": "Valor estimado :",
        "STEPS": "PASOS",
        "(no steps created)": "(ningún paso creado)",
        "DONE": "LISTO",
        "IN PROGRESS": "EN CURSO",
        "PAUSED": "PAUSADO",
        "PENDING": "PENDIENTE",
        "start:": "inicio:",
        "end:": "fin:",
        "now (in progress)": "ahora (en curso)",
        "Summary: {d}/{n} done": "Resumen: {d}/{n} listos",
        "SESSIONS HISTORY": "HISTORIAL DE SESIONES",
        "(no finished sessions logged)": "(ninguna sesión finalizada registrada)",
        "session": "sesión",
        "total": "total",
        "SETTINGS USED": "AJUSTES USADOS",
        "Pause when unfocused :": "Pausa sin foco :",
        "Pause when idle     :": "Pausa inactivo  :",
        "YES": "SÍ",
        "NO": "NO",
        "({m} min)": "({m} min)",
        "Generated by the Track Timer addon": "Generado por el addon Track Timer",
        "Render: {t}": "Render: {t}",
        "(recovered)": "(recuperada)",
        "Allowed apps (e.g. PureRef, Photoshop)": "Apps permitidas (ej.: PureRef, Photoshop)",
        "Comma-separated names. When one of these apps is focused, it still counts as work": "Nombres separados por comas. Cuando una de estas apps tiene el foco, sigue contando como trabajo",
        "Focus grace (s)": "Tolerancia de foco (s)",
        "Seconds of lost focus tolerated before pausing (quick Alt+Tab)": "Segundos sin foco tolerados antes de pausar (Alt+Tab rápido)",
        "Step time mode": "Modo de tiempo",
        "How time is shared when several steps are active at once": "Cómo se reparte el tiempo con varios pasos activos",
        "Count in parallel": "Contar en paralelo",
        "Split between active steps": "Dividir entre pasos activos",
        "Currency symbol": "Símbolo de moneda",
        "Optional symbol (empty = automatic per language)": "Símbolo opcional (vacío = automático por idioma)",
        "Tip: install xdotool and xprintidle for focus + idle detection": "Consejo: instala xdotool y xprintidle para detección de foco + inactividad",
        "Print / Save as PDF": "Imprimir / Guardar en PDF",
        "Project:": "Proyecto:",
        "Client:": "Cliente:",
        "Status": "Estado",
        "Time": "Tiempo",
        "Start time": "Inicio",
        "End": "Fin",
        "Session": "Sesión",
        "Total": "Total",
        "General": "General",
        "Animation": "Animación",
        "Archviz": "Archviz",
        "Motion": "Motion",
        "Extras:": "Extras:",
        "Example outline": "Guía de ejemplo",
        "REFERENCES": "REFERENCIAS",
        "SPLINE": "SPLINE",
        "POLISH": "PULIDO",
        "PLAYBLAST": "PLAYBLAST",
        "FINAL RENDER": "RENDER FINAL",
        "DELIVERY": "ENTREGA",
        "MODELING": "MODELADO",
        "MATERIALS": "MATERIALES",
        "STORYBOARD": "STORYBOARD",
        "STYLEFRAMES": "STYLEFRAMES",
        "ANIMATION": "ANIMACIÓN",
        "COMPOSITING": "COMPOSICIÓN",
        "Generate HTML report": "Generar informe HTML",
        "Generate a printable HTML report (open in a browser, print to PDF)": "Genera un informe HTML imprimible (ábrelo en el navegador, imprime en PDF)",
        "Also generate HTML report": "Generar informe HTML también",
        "Write a printable HTML version next to the TXT on every report": "Guarda una versión HTML imprimible junto al TXT en cada informe",
        "Show timer overlay in viewport": "Mostrar reloj en el viewport",
        "Always-visible clock in the 3D viewport (may cost redraws in heavy scenes)": "Reloj siempre visible en el viewport 3D (puede costar redibujados en escenas pesadas)",
        "Show today / week": "Mostrar hoy / semana",
        "Show today's and this week's hours in the panel": "Muestra las horas de hoy y de la semana en el panel",
        "Client name": "Nombre del cliente",
        "Shown in the HTML report header": "Se muestra en el encabezado del informe HTML",
        "Project name": "Nombre del proyecto",
        "Shown in the HTML report header (empty = .blend name)": "Se muestra en el encabezado del informe HTML (vacío = nombre del .blend)",
        "Today: {t}": "Hoy: {t}",
        "This week: {t}": "Semana: {t}",
        "Render": "Render",
        "Folder:": "Carpeta:",
        "Generated:": "Generado:",
        "Allow app": "Permitir app",
        "Add this app to the allowed list (counts as work when focused)": "Añade esta app a la lista (cuenta como trabajo con foco)",
        "Remove app": "Quitar app",
        "Remove this app from the allowed list": "Quita esta app de la lista",
        "Add focused app": "Añadir app enfocada",
        "Add the last app seen in focus (switch to it first if the list is empty)": "Añade la última app vista con foco (cambia a ella antes si la lista está vacía)",
        "No other app seen yet — switch to it first": "Ninguna otra app vista aún — cambia a ella antes",
        "'{n}' will now count as work": "'{n}' ahora cuenta como trabajo",
        "'{n}' removed from allowed": "'{n}' quitada de permitidas",
        "Work apps (counted as work even when focused):": "Apps de trabajo (cuentan aun con foco):",
        "(none — only Blender counts)": "(ninguna — solo Blender cuenta)",
        "Type to filter:": "Escribe para filtrar:",
        "Add \"{x}\"": "Añadir \"{x}\"",
        "Focused: {x}": "En foco: {x}",
        "Blender (this window)": "Blender (esta ventana)",
        "unknown": "desconocido",
        "Preferences unavailable": "Preferencias no disponibles",
        "Client": "Cliente",
        "Project": "Proyecto",
        "Client / Project": "Cliente / Proyecto",
        "Show client header": "Mostrar encabezado de cliente",
        "Show the client/project fields at the top of the panel (fill in first)": "Muestra los campos cliente/proyecto arriba del panel (rellena primero)",
        "Step auto-start": "Auto-inicio de pasos",
        "Automatically start step 1 on new outlines and advance to the next step on finish": "Inicia el paso 1 en guías nuevas y avanza al siguiente al terminar",
        "Avg session": "Sesión media",
        "avg of {n} sessions": "media de {n} sesiones",
        "Average session": "Sesión media",
        "Show the average session time in the report (from all logged sessions)": "Muestra el tiempo medio por sesión en el informe (de todas las sesiones)",
        "Client    :": "Cliente   :",
        "Start on first edit or save": "Iniciar al primer uso (editar o guardar)",
        "Start counting on the first scene change or save while everything is still zeroed, so no work goes untracked": "Inicia el conteo con el primer cambio o guardado, con todo en cero",
    },
    "fr": {
        "Start": "Démarrer",
        "Start / resume counting": "Démarre / reprend le comptage",
        "Pause": "Pause",
        "Pause counting (keeps the total)": "Met en pause (conserve le total)",
        "Finish session": "Terminer la session",
        "Stop counting and log the session to the .csv/.json in the reports folder": "Arrête le comptage et enregistre la session dans le .csv/.json du dossier de rapports",
        "Reset total": "Réinitialiser le total",
        "Reset total and session (to start a new model). Does NOT delete steps (use Clear steps for that)": "Réinitialise le total et la session (pour un nouveau modèle). Ne supprime PAS les étapes (voir Effacer terminées)",
        "Adjust time": "Ajuster le temps",
        "Manual adjustment (e.g. forgot to start, or counted non-work time)": "Ajustement manuel (ex. oubli de démarrage, ou temps compté hors travail)",
        "Minutes (+/-)": "Minutes (+/-)",
        "Export CSV": "Exporter CSV",
        "Update the .tracktime.csv and .milestones.csv in the reports folder": "Met à jour .tracktime.csv et .milestones.csv dans le dossier de rapports",
        "Generate report now": "Générer le rapport",
        "Generate the TXT report in the reports folder, with the content chosen on the settings page": "Génère le rapport TXT dans le dossier de rapports, avec le contenu choisi dans les réglages",
        "Open reports folder": "Ouvrir le dossier de rapports",
        "Open the folder with the TXT report and CSVs": "Ouvre le dossier avec le rapport TXT et les CSV",
        "Add step": "Ajouter une étape",
        "Add a step (you can add before or during counting)": "Ajoute une étape (avant ou pendant le comptage)",
        "Step name": "Nom de l'étape",
        "Start now": "Commencer maintenant",
        "If on, the step is born marked as 'in progress' (you can mark several at the same time)": "Si activé, l'étape naît marquée « en cours » (plusieurs possibles)",
        "Remove step": "Supprimer l'étape",
        "Remove the selected step": "Supprime l'étape sélectionnée",
        "Start / Pause step": "Démarrer / Pause étape",
        "Mark/unmark 'I'm working on this right now'. You can keep SEVERAL active at the same time. If the global timer is stopped, it starts by itself": "Marque/décoche « je travaille dessus maintenant ». Plusieurs étapes actives possibles. Si le minuteur global est arrêté, il démarre seul",
        "Done! / Reopen": "Terminé ! / Rouvrir",
        "Mark the step as DONE (freezes its time) or reopen a finished step": "Marque l'étape comme TERMINÉE (fige son temps) ou rouvre une étape terminée",
        "Move step": "Déplacer l'étape",
        "Move the step up/down in the list": "Monte/descend l'étape dans la liste",
        "Clear finished": "Effacer terminées",
        "Remove all finished steps from the list (keeps the open ones)": "Supprime de la liste toutes les étapes terminées (garde les ouvertes)",
        "Load example outline": "Charger un exemple d'étapes",
        "Add example steps (Blocking, Modeling, UV, Texturing...) — skips ones that already exist": "Ajoute des étapes d'exemple (Blocking, Modélisation, UV, Textures...) — ignore celles qui existent",
        "Adjust step": "Ajuster l'étape",
        "Manual time adjustment of the selected step": "Ajustement manuel du temps de l'étape sélectionnée",
        "Counting": "Comptage",
        "Total (s)": "Total (s)",
        "Session (s)": "Session (s)",
        "Pause reason": "Raison de pause",
        "Pause when Blender loses focus": "Pause si Blender perd le focus",
        "If on: minimized, switched window/app or watching a video = pause. If off: it counts straight until you pause/finish": "Si activé : minimisé, autre fenêtre/app ou vidéo = pause. Sinon : comptage continu jusqu'à pause/fin",
        "Pause when idle": "Pause si inactif",
        "Pauses even with Blender in front if there is no keyboard/mouse for X minutes (coffee break). Windows only.": "Pause même si Blender est au premier plan sans clavier/souris pendant X minutes (pause café). Windows uniquement.",
        "Idle (min)": "Inactivité (min)",
        "Minutes without keyboard/mouse to count as idle": "Minutes sans clavier/souris pour compter comme inactif",
        "Rate / hour": "Tarif / heure",
        "Optional: to estimate the job value": "Optionnel : pour estimer la valeur du travail",
        "Show in status bar": "Afficher dans la barre d'état",
        "Auto backup next to the .blend": "Sauvegarde auto près du .blend",
        "Saves .tracktime.json next to the .blend every 30s and on finish, so no time is lost if you close without saving": "Enregistre .tracktime.json près du .blend toutes les 30 s et à la fin, pour ne rien perdre sans sauvegarde",
        "Selected step": "Étape sélectionnée",
        "Session started at": "Session démarrée à",
        "Time the current session started (used in the report)": "Heure de début de la session (utilisée dans le rapport)",
        "Project started at": "Projet démarré à",
        "Time work on this file started (used in the report)": "Heure de début du travail sur ce fichier (utilisée dans le rapport)",
        "Last report": "Dernier rapport",
        "Path of the last generated TXT report": "Chemin du dernier rapport TXT généré",
        "Step": "Étape",
        "ID": "ID",
        "Stable step identity (internal: protects time against Ctrl+Z)": "Identité stable de l'étape (interne : protège le temps contre Ctrl+Z)",
        "In progress": "En cours",
        "Marked = you are working on THIS step right now. You can mark several at the same time": "Coché = vous travaillez sur CETTE étape maintenant. Plusieurs possibles",
        "Done": "Terminée",
        "Marked = finished step, frozen time": "Coché = étape terminée, temps figé",
        "Seconds": "Secondes",
        "Created at": "Créée le",
        "Finished at": "Terminée le",
        "Header (project, folder, date)": "En-tête (projet, dossier, date)",
        "Hours spent (total)": "Heures (total)",
        "Current session hours": "Heures de la session",
        "Period (start-end time)": "Période (heure début-fin)",
        "Shows project start, session start and end": "Affiche début du projet, début et fin de session",
        "Estimated value": "Valeur estimée",
        "Steps table": "Tableau des étapes",
        "Lists each step with status, time, start and end": "Liste chaque étape avec statut, temps, début et fin",
        "Sessions history": "Historique des sessions",
        "Settings used": "Réglages utilisés",
        "Generate/update on save and session finish": "Générer/actualiser à l'enregistrement et en fin de session",
        "Updates the TXT in the reports folder whenever you save the .blend or finish a session": "Met à jour le TXT dans le dossier de rapports à chaque enregistrement ou fin de session",
        "Generate when Blender closes": "Générer à la fermeture de Blender",
        "Tries to update the TXT when quitting Blender (via exit auto-save)": "Tente de mettre à jour le TXT en quittant Blender (sauvegarde de sortie)",
        "File suffix": "Suffixe de fichier",
        "E.g. _REPORT creates 'mymodel_REPORT.txt' in the reports folder": "Ex. _RAPPORT crée « monmodele_RAPPORT.txt » dans le dossier de rapports",
        "Language": "Langue",
        "Reports folder name": "Nom du dossier de rapports",
        "Folder created next to the .blend to hold the TXT report and CSVs": "Dossier créé près du .blend pour le rapport TXT et les CSV",
        "What goes into the TXT report ({folder}):": "Contenu du rapport TXT ({folder}) :",
        "Automatic:": "Automatique :",
        "COUNTING...": "COMPTAGE...",
        "STOPPED": "ARRÊTÉ",
        "PAUSED — Blender unfocused": "PAUSE — Blender sans focus",
        "PAUSED — idle for {m}min": "PAUSE — inactif depuis {m} min",
        "Total: {t}": "Total : {t}",
        "Session: {t}": "Session : {t}",
        "Est. value:": "Valeur est. :",
        "currency_symbol": "€",
        "Steps  •  {a} in progress  •  {d}/{n} done": "Étapes  •  {a} en cours  •  {d}/{n} terminées",
        "Selected: {n} — {t}": "Sélectionnée : {n} — {t}",
        "  [DONE]": "  [TERMINÉE]",
        "  [WORKING NOW]": "  [EN COURS]",
        "Pause step": "Pause étape",
        "Start step": "Démarrer l'étape",
        "Reopen": "Rouvrir",
        "DONE!": "TERMINÉ !",
        "No steps. Add BLOCKING, etc.": "Aucune étape. Ajoutez BLOCKING, etc.",
        "Global timer stopped: active steps don't count.": "Minuteur global arrêté : les étapes actives ne comptent pas.",
        "TXT report (reports folder)": "Rapport TXT (dossier de rapports)",
        "Last: {f}": "Dernier : {f}",
        "Content in Preferences > Add-ons > Track Timer": "Contenu dans Preferences > Add-ons > Track Timer",
        "Focus/idle auto: Windows only.": "Focus/inactivité auto : Windows uniquement.",
        "On Linux/Mac it counts straight.": "Sous Linux/Mac, comptage continu.",
        "Save the .blend to enable .json/.csv backup": "Enregistrez le .blend pour la copie .json/.csv",
        "{n} steps": "{n} étapes",
        "BLOCKING": "BLOCKING",
        "DETAILED MODELING": "MODÉLISATION DÉTAILLÉE",
        "RETOPOLOGY": "RETOPOLOGIE",
        "TEXTURING": "TEXTURES",
        "LIGHTING": "ÉCLAIRAGE",
        "POST / DELIVERY": "POST-PROD / LIVRAISON",
        "Step {n}": "Étape {n}",
        "Track Timer: counting started": "Track Timer : comptage démarré",
        "Track Timer: paused": "Track Timer : en pause",
        "Track Timer: session of {s} logged. Total: {t}": "Track Timer : session de {s} enregistrée. Total : {t}",
        "Track Timer: total reset (steps kept)": "Track Timer : total réinitialisé (étapes gardées)",
        "Track Timer: total adjusted to {t}": "Track Timer : total ajusté à {t}",
        "Track Timer: CSVs updated in the reports folder": "Track Timer : CSV mis à jour dans le dossier de rapports",
        "Save the .blend first (reports live in its folder)": "Enregistrez d'abord le .blend (les rapports vont dans son dossier)",
        "Step '{n}' added": "Étape « {n} » ajoutée",
        "Step '{n}' removed": "Étape « {n} » supprimée",
        "No step selected": "Aucune étape sélectionnée",
        "'{n}' already finished — reopen it to continue": "« {n} » déjà terminée — rouvrez-la pour continuer",
        "'{n}' in progress (timer started)": "« {n} » en cours (minuteur démarré)",
        "'{n}' in progress": "« {n} » en cours",
        "'{n}' paused (kept time: {t})": "« {n} » en pause (temps gardé : {t})",
        "'{n}' DONE in {t}": "« {n} » TERMINÉE en {t}",
        "'{n}' reopened": "« {n} » rouverte",
        "'{n}' adjusted to {t}": "« {n} » ajustée à {t}",
        "{n} example steps added": "{n} étapes d'exemple ajoutées",
        "Outline already exists": "L'exemple existe déjà",
        "Report saved: {p}": "Rapport enregistré : {p}",
        "Could not generate the report": "Rapport non généré",
        "Save the .blend first (the report lives in its folder)": "Enregistrez d'abord le .blend (le rapport va dans son dossier)",
        "Folder: {f}": "Dossier : {f}",
        "TIME REPORT — TRACK TIMER": "RAPPORT D'HEURES — TRACK TIMER",
        "Project   :": "Projet    :",
        "Folder    :": "Dossier   :",
        "Generated :": "Généré le :",
        "(reason: {r})": "(raison : {r})",
        "manual": "manuel",
        "save": "enregistrement",
        "session finished": "session terminée",
        "project switch": "changement de projet",
        "exit": "sortie",
        "PERIOD (start-end time)": "PÉRIODE (heure début-fin)",
        "Project start :": "Début du projet :",
        "Session start :": "Début de session :",
        "Session end   :": "Fin de session    :",
        "(in progress)": "(en cours)",
        "Current session : none (click Start)": "Session actuelle    : aucune (cliquez sur Démarrer)",
        "HOURS SPENT": "HEURES",
        "Total   :": "Total   :",
        "Session :": "Session :",
        "VALUE": "VALEUR",
        "Rate/hour     :": "Tarif/heure    :",
        "Estimated value :": "Valeur estimée :",
        "STEPS": "ÉTAPES",
        "(no steps created)": "(aucune étape créée)",
        "DONE": "TERMINÉE",
        "IN PROGRESS": "EN COURS",
        "PAUSED": "EN PAUSE",
        "PENDING": "EN ATTENTE",
        "start:": "début :",
        "end:": "fin :",
        "now (in progress)": "maintenant (en cours)",
        "Summary: {d}/{n} done": "Résumé : {d}/{n} terminées",
        "SESSIONS HISTORY": "HISTORIQUE DES SESSIONS",
        "(no finished sessions logged)": "(aucune session terminée enregistrée)",
        "session": "session",
        "total": "total",
        "SETTINGS USED": "RÉGLAGES UTILISÉS",
        "Pause when unfocused :": "Pause sans focus :",
        "Pause when idle     :": "Pause inactif   :",
        "YES": "OUI",
        "NO": "NON",
        "({m} min)": "({m} min)",
        "Generated by the Track Timer addon": "Généré par l'addon Track Timer",
        "Render: {t}": "Rendu : {t}",
        "(recovered)": "(récupérée)",
        "Allowed apps (e.g. PureRef, Photoshop)": "Apps autorisées (ex. PureRef, Photoshop)",
        "Comma-separated names. When one of these apps is focused, it still counts as work": "Noms séparés par des virgules. Quand l'une de ces apps a le focus, ça compte comme travail",
        "Focus grace (s)": "Tolérance de focus (s)",
        "Seconds of lost focus tolerated before pausing (quick Alt+Tab)": "Secondes sans focus tolérées avant la pause (Alt+Tab rapide)",
        "Step time mode": "Mode de temps des étapes",
        "How time is shared when several steps are active at once": "Répartition du temps avec plusieurs étapes actives",
        "Count in parallel": "Compter en parallèle",
        "Split between active steps": "Diviser entre étapes actives",
        "Currency symbol": "Symbole monétaire",
        "Optional symbol (empty = automatic per language)": "Symbole optionnel (vide = auto par langue)",
        "Tip: install xdotool and xprintidle for focus + idle detection": "Astuce : installez xdotool et xprintidle pour la détection focus + inactivité",
        "Print / Save as PDF": "Imprimer / Enregistrer en PDF",
        "Project:": "Projet :",
        "Client:": "Client :",
        "Status": "Statut",
        "Time": "Temps",
        "Start time": "Début",
        "End": "Fin",
        "Session": "Session",
        "Total": "Total",
        "General": "Général",
        "Animation": "Animation",
        "Archviz": "Archviz",
        "Motion": "Motion",
        "Extras:": "Extras :",
        "Example outline": "Exemple d'étapes",
        "REFERENCES": "RÉFÉRENCES",
        "SPLINE": "SPLINE",
        "POLISH": "FINITION",
        "PLAYBLAST": "PLAYBLAST",
        "FINAL RENDER": "RENDU FINAL",
        "DELIVERY": "LIVRAISON",
        "MODELING": "MODÉLISATION",
        "MATERIALS": "MATÉRIAUX",
        "STORYBOARD": "STORYBOARD",
        "STYLEFRAMES": "STYLEFRAMES",
        "ANIMATION": "ANIMATION",
        "COMPOSITING": "COMPOSITING",
        "Generate HTML report": "Générer le rapport HTML",
        "Generate a printable HTML report (open in a browser, print to PDF)": "Génère un rapport HTML imprimable (navigateur, impression PDF)",
        "Also generate HTML report": "Générer aussi le HTML",
        "Write a printable HTML version next to the TXT on every report": "Écrit une version HTML imprimable avec le TXT à chaque rapport",
        "Show timer overlay in viewport": "Afficher l'horloge dans le viewport",
        "Always-visible clock in the 3D viewport (may cost redraws in heavy scenes)": "Horloge toujours visible dans le viewport 3D (redessins coûteux en scènes lourdes)",
        "Show today / week": "Afficher jour / semaine",
        "Show today's and this week's hours in the panel": "Affiche les heures du jour et de la semaine dans le panneau",
        "Client name": "Nom du client",
        "Shown in the HTML report header": "Affiché dans l'en-tête du rapport HTML",
        "Project name": "Nom du projet",
        "Shown in the HTML report header (empty = .blend name)": "Affiché dans l'en-tête du rapport HTML (vide = nom du .blend)",
        "Today: {t}": "Aujourd'hui : {t}",
        "This week: {t}": "Semaine : {t}",
        "Render": "Rendu",
        "Folder:": "Dossier :",
        "Generated:": "Généré le :",
        "Allow app": "Autoriser l'app",
        "Add this app to the allowed list (counts as work when focused)": "Ajoute cette app à la liste (compte comme travail avec focus)",
        "Remove app": "Retirer l'app",
        "Remove this app from the allowed list": "Retire cette app de la liste",
        "Add focused app": "Ajouter l'app active",
        "Add the last app seen in focus (switch to it first if the list is empty)": "Ajoute la dernière app vue avec focus (basculez d'abord dessus si la liste est vide)",
        "No other app seen yet — switch to it first": "Aucune autre app vue — basculez d'abord dessus",
        "'{n}' will now count as work": "« {n} » compte désormais comme travail",
        "'{n}' removed from allowed": "« {n} » retirée des autorisées",
        "Work apps (counted as work even when focused):": "Apps de travail (comptent même avec focus) :",
        "(none — only Blender counts)": "(aucune — seul Blender compte)",
        "Type to filter:": "Tapez pour filtrer :",
        "Add \"{x}\"": "Ajouter « {x} »",
        "Focused: {x}": "Focus : {x}",
        "Blender (this window)": "Blender (cette fenêtre)",
        "unknown": "inconnu",
        "Preferences unavailable": "Préférences indisponibles",
        "Client": "Client",
        "Project": "Projet",
        "Client / Project": "Client / Projet",
        "Show client header": "Afficher l'en-tête client",
        "Show the client/project fields at the top of the panel (fill in first)": "Affiche les champs client/projet en haut du panneau (à remplir d'abord)",
        "Step auto-start": "Démarrage auto des étapes",
        "Automatically start step 1 on new outlines and advance to the next step on finish": "Démarre l'étape 1 sur un nouvel exemple et avance à la suivante en finissant",
        "Avg session": "Session moyenne",
        "avg of {n} sessions": "moyenne de {n} sessions",
        "Average session": "Session moyenne",
        "Show the average session time in the report (from all logged sessions)": "Affiche le temps moyen par session dans le rapport (toutes sessions)",
        "Client    :": "Client    :",
        "Start on first edit or save": "Démarrer au premier usage (édition/sauvegarde)",
        "Start counting on the first scene change or save while everything is still zeroed, so no work goes untracked": "Démarre le comptage au premier changement ou enregistrement, à zéro",
    },
}


def get_lang() -> str:
    """Active language code (settings page). Defaults to English US."""
    try:
        prefs = _addon_prefs()
        if prefs is not None and hasattr(prefs, "language"):
            code = getattr(prefs, "language")
            if code in STRINGS:
                return code
    except Exception:
        pass
    return "en_US"


def T(text: str) -> str:
    """Translate an English source string. Falls back to English."""
    try:
        lang = get_lang()
        if lang != "en_US":
            tr = STRINGS.get(lang, {}).get(text)
            if tr:
                return tr
    except Exception:
        pass
    return text


def _apply_language():
    """Refresh operator/panel labels after a language switch (no restart)."""
    try:
        for cls in classes:
            lk = getattr(cls, "_label_key", None)
            if lk:
                cls.bl_label = T(lk)
            dk = getattr(cls, "_desc_key", None)
            if dk:
                cls.bl_description = T(dk)
    except Exception:
        pass


def _update_language(self, context):
    _apply_language()


# -------------------------------------------------------------------
# Utilidades de tempo / foco / ociosidade
# -------------------------------------------------------------------

def format_hms(seconds: float) -> str:
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


_IS_WINDOWS = platform.system() == "Windows"
_IS_MAC = platform.system() == "Darwin"
_IS_LINUX = platform.system() == "Linux"

import shutil
import subprocess

# --- Windows API handles (with strict signatures) ---
_ctypes = None
_wintypes = None
_user32 = None
_kernel32 = None
_psapi = None
_LastInputInfo = None
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
try:
    if _IS_WINDOWS:
        import ctypes as _ctypes_mod
        from ctypes import wintypes as _wintypes_mod
        _ctypes = _ctypes_mod
        _wintypes = _wintypes_mod
        _user32 = _ctypes.windll.user32
        _kernel32 = _ctypes.windll.kernel32
        _psapi = _ctypes.windll.psapi
        _user32.GetForegroundWindow.restype = _wintypes.HWND
        _user32.GetForegroundWindow.argtypes = []
        _user32.GetWindowThreadProcessId.restype = _wintypes.DWORD
        _user32.GetWindowThreadProcessId.argtypes = [
            _wintypes.HWND, _ctypes.POINTER(_wintypes.DWORD)]
        _user32.GetLastInputInfo.restype = _wintypes.BOOL
        _user32.GetLastInputInfo.argtypes = [_ctypes.c_void_p]
        _kernel32.GetTickCount64.restype = _ctypes.c_ulonglong
        _kernel32.GetTickCount64.argtypes = []
        _kernel32.OpenProcess.restype = _wintypes.HANDLE
        _kernel32.OpenProcess.argtypes = [
            _wintypes.DWORD, _wintypes.BOOL, _wintypes.DWORD]
        _kernel32.CloseHandle.restype = _wintypes.BOOL
        _kernel32.CloseHandle.argtypes = [_wintypes.HANDLE]
        _psapi.GetModuleBaseNameW.restype = _wintypes.DWORD
        _psapi.GetModuleBaseNameW.argtypes = [
            _wintypes.HANDLE, _wintypes.HMODULE,
            _wintypes.LPWSTR, _wintypes.DWORD]
        _kernel32.QueryFullProcessImageNameW.restype = _wintypes.BOOL
        _kernel32.QueryFullProcessImageNameW.argtypes = [
            _wintypes.HANDLE, _wintypes.DWORD,
            _wintypes.LPWSTR, _ctypes.POINTER(_wintypes.DWORD)]
        _user32.GetWindowTextLengthW.restype = _ctypes.c_int
        _user32.GetWindowTextLengthW.argtypes = [_wintypes.HWND]
        _user32.GetWindowTextW.restype = _ctypes.c_int
        _user32.GetWindowTextW.argtypes = [
            _wintypes.HWND, _wintypes.LPWSTR, _ctypes.c_int]

        class _LastInputInfo(_ctypes.Structure):
            _fields_ = [("cbSize", _wintypes.UINT),
                        ("dwTime", _wintypes.DWORD)]
except Exception:
    _user32 = None
    _kernel32 = None
    _psapi = None
    _LastInputInfo = None


# --- backend detection (focus + idle per OS) ---
_BACKEND = {"focus": None, "idle": None}


def _have_tool(name: str) -> bool:
    try:
        return shutil.which(name) is not None
    except Exception:
        return False


def _probe_backends():
    """Detecta o backend de foco/ociosidade. Roda no register e no load."""
    if _IS_WINDOWS and _user32 is not None:
        _BACKEND["focus"] = "windows"
        _BACKEND["idle"] = "windows"
    elif _IS_LINUX:
        _BACKEND["focus"] = "xdotool" if _have_tool("xdotool") else None
        _BACKEND["idle"] = "xprintidle" if _have_tool("xprintidle") else None
    elif _IS_MAC:
        _BACKEND["focus"] = "osascript" if _have_tool("osascript") else None
        _BACKEND["idle"] = "ioreg" if _have_tool("ioreg") else None
    else:
        _BACKEND["focus"] = None
        _BACKEND["idle"] = None
    return _BACKEND


def _run_capture(argv, timeout=2.0):
    try:
        out = subprocess.run(argv, capture_output=True, text=True,
                             timeout=timeout, check=False)
        return (out.returncode, (out.stdout or "").strip())
    except Exception:
        return (None, "")


_throttle_cache = {}


def _throttled(key, interval_s, fn):
    now = time.monotonic()
    hit = _throttle_cache.get(key)
    if hit is not None and (now - hit[0]) < interval_s:
        return hit[1]
    val = fn()
    _throttle_cache[key] = (now, val)
    return val


# --- Windows fetchers ---
def _win_fg_hwnd():
    """Foreground window handle. 0 = no focused window. None = unavailable."""
    if _user32 is None:
        return None
    try:
        return int(_user32.GetForegroundWindow() or 0)
    except Exception:
        return None


def _win_pid_of(hwnd):
    try:
        if not hwnd or _user32 is None:
            return None
        pid = _wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, _ctypes.byref(pid))
        return int(pid.value)
    except Exception:
        return None


def _win_window_text(hwnd):
    try:
        if not hwnd or _user32 is None:
            return ""
        n = int(_user32.GetWindowTextLengthW(hwnd) or 0)
        if n <= 0:
            return ""
        size = min(n + 1, 512)
        buf = _ctypes.create_unicode_buffer(size)
        if _user32.GetWindowTextW(hwnd, buf, size) > 0:
            return buf.value or ""
        return ""
    except Exception:
        return ""


def _win_process_name(pid):
    if not pid or _kernel32 is None or _psapi is None:
        return None
    try:
        h = _kernel32.OpenProcess(
            _PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not h:
            return None
        try:
            buf = _ctypes.create_unicode_buffer(260)
            if _psapi.GetModuleBaseNameW(h, None, buf, 260) and buf.value:
                return buf.value
            # fallback: full image path (GetModuleBaseName fails
            # with access-denied on Chrome and similar processes)
            try:
                buf2 = _ctypes.create_unicode_buffer(260)
                size = _wintypes.DWORD(260)
                if _kernel32.QueryFullProcessImageNameW(
                        h, 0, buf2, _ctypes.byref(size)) and buf2.value:
                    return os.path.basename(buf2.value)
            except Exception:
                pass
            return None
        finally:
            try:
                _kernel32.CloseHandle(h)
            except Exception:
                pass
    except Exception:
        return None


def _win_idle_seconds() -> float:
    if _user32 is None or _kernel32 is None or _LastInputInfo is None:
        return 0.0
    try:
        lii = _LastInputInfo()
        lii.cbSize = _ctypes.sizeof(_LastInputInfo)
        if not _user32.GetLastInputInfo(_ctypes.byref(lii)):
            return 0.0
        now = _kernel32.GetTickCount64()
        return max(0.0, (now - lii.dwTime) / 1000.0)
    except Exception:
        return 0.0


# --- Linux fetchers (xdotool / /proc / xprintidle) ---
def _linux_fg_pid():
    if not _have_tool("xdotool"):
        return None
    try:
        _code, out = _run_capture(
            ["xdotool", "getwindowfocus", "getwindowpid"])
        nums = [int(x) for x in out.split() if x.strip().isdigit()]
        if not nums:
            return 0
        return nums[-1]
    except Exception:
        return None


def _linux_process_name(pid):
    try:
        if not pid:
            return None
        with open(f"/proc/{int(pid)}/comm", "r", encoding="utf-8") as f:
            return (f.read() or "").strip() or None
    except Exception:
        return None


def _linux_idle_seconds() -> float:
    try:
        _code, out = _run_capture(["xprintidle"])
        return max(0.0, int(out.strip()) / 1000.0)
    except Exception:
        return 0.0


# --- macOS fetchers (osascript / ioreg, both ship with the OS) ---
def _mac_front_info():
    """(pid_or_None, name_or_None) of the frontmost process."""
    try:
        _code, out = _run_capture([
            "osascript", "-e",
            'tell application "System Events" to get '
            '{name, unix id} of first process whose frontmost is true'])
        if "," not in out:
            return (None, None)
        name, pid = out.rsplit(",", 1)
        return (int(pid.strip()), name.strip() or None)
    except Exception:
        return (None, None)


def _mac_idle_seconds() -> float:
    try:
        import re as _re
        _code, out = _run_capture(["ioreg", "-c", "IOHIDSystem"])
        vals = [int(x) for x in _re.findall(r"HIDIdleTime[^=]*=\s*(\d+)", out)]
        if not vals:
            return 0.0
        return max(0.0, max(vals) / 1e9)
    except Exception:
        return 0.0


def _linux_fg_title():
    try:
        if not _have_tool("xdotool"):
            return ""
        _code, out = _run_capture(
            ["xdotool", "getwindowfocus", "getwindowname"])
        return out.strip() or ""
    except Exception:
        return ""


def fg_info():
    """(pid, process_name, window_title). pid None = no backend; 0 = nothing focused."""
    fb = _BACKEND.get("focus")
    if fb == "windows":
        try:
            hwnd = _win_fg_hwnd()
        except Exception:
            return (None, None, None)
        if hwnd is None:
            return (None, None, None)
        if not hwnd:
            return (0, None, None)
        pid = _win_pid_of(hwnd)
        if pid is None:
            return (None, None, None)
        return (pid, _win_process_name(pid), _win_window_text(hwnd))
    if fb == "xdotool":
        pid = _throttled("fg", 2.0, _linux_fg_pid)
        if pid is None:
            return (None, None, None)
        if not pid:
            return (0, None, None)
        title = _throttled("fgtitle", 2.0, _linux_fg_title)
        return (pid, _linux_process_name(pid), title)
    if fb == "osascript":
        pid, name = _throttled("fg", 2.0, _mac_front_info)
        if pid is None:
            return (None, None, None)
        if not pid:
            return (0, None, None)
        return (pid, name, "")
    return (None, None, None)


def is_blender_focused() -> bool:
    """True if the foreground window belongs to this Blender process.

    No backend (or backend error) means True — count straight.
    Allowed companion apps are handled by the caller via fg_info().
    """
    try:
        pid, _name, _title = fg_info()
    except Exception:
        return True
    if pid is None:
        return True
    if not pid:
        return False  # nothing focused (lock screen etc.) = paused
    try:
        return int(pid) == int(os.getpid())
    except Exception:
        return True


def get_idle_seconds() -> float:
    """Seconds since last keyboard/mouse input. 0.0 if unavailable."""
    try:
        ib = _BACKEND.get("idle")
        if ib == "windows":
            return _win_idle_seconds()
        if ib == "xprintidle":
            return _throttled("idle", 2.0, _linux_idle_seconds)
        if ib == "ioreg":
            return _throttled("idle", 2.0, _mac_idle_seconds)
    except Exception:
        pass
    return 0.0


def _norm_app(s) -> str:
    s = (s or "").strip().lower()
    if s.endswith(".exe"):
        s = s[:-4]
    return s


def _allowed_apps_list():
    try:
        prefs = _addon_prefs()
        raw = getattr(prefs, "allowed_apps", "") if prefs is not None else ""
    except Exception:
        raw = ""
    return [a for a in (_norm_app(x) for x in (raw or "").split(",")) if a]


def fg_matches_allowed(proc_name, title=None) -> bool:
    """True if an allowlist entry matches the process name OR window title."""
    cands = [_norm_app(proc_name)]
    if title:
        cands.append(_norm_app(title))
    cands = [c for c in cands if c]
    if not cands:
        return False
    try:
        allowed = _allowed_apps_list()
    except Exception:
        return False
    try:
        for cand in cands:
            for a in allowed:
                if a and (a in cand):
                    return True
    except Exception:
        pass
    return False


# -------------------------------------------------------------------
# Undo-proof in-memory store (Ctrl+Z can't touch plain Python)
# -------------------------------------------------------------------
# The TRUTH lives here. Scene props are only the "display".
# - File totals:  _file_state[filepath] = total/session/running/render
# - Step detail:  _time_store[(filepath, scene)] = ms {uid: {s,a,d}}
# Props are written only on change (int compare), every ~20 s, on
# operators, and before save (save_pre) — never every tick.

_time_store = {}
_file_state = {}
# files the user deliberately paused/finished: auto-triggers stay away
# until load/reset. Cleared on file open so opening never counts blank.
_paused_files = set()

_last_tick_mono = None
_last_sidecar_save = 0.0
_last_props_sync = 0.0
_last_drawn_int = None
_unfocused_since = None
_render_active = False
_render_start_mono = 0.0


def _file_key() -> str:
    try:
        return bpy.data.filepath or "<unsaved>"
    except Exception:
        return "<unsaved>"


def _store_key_for_scene(scene) -> tuple:
    try:
        name = scene.name if scene is not None else "<noscene>"
    except Exception:
        name = "<noscene>"
    return (_file_key(), name)


def _read_sidecar():
    """Raw sidecar JSON dict, or None."""
    try:
        path = sidecar_path_for_blend()
        if not path or not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _file_entry() -> dict:
    """File-level truth, adopting visible values when new.

    Legacy multi-scene files: identical totals everywhere mean "already
    file-level" (take it); divergent totals mean per-scene counting from
    older versions (sum them). Then keep the max with the sidecar.
    Never erases visible time.
    """
    key = _file_key()
    entry = _file_state.get(key)
    if entry is not None:
        return entry
    entry = {"total": 0.0, "session": 0.0, "running": False, "render": 0.0}
    _file_state[key] = entry
    try:
        totals, renders = [], []
        for s in bpy.data.scenes:
            try:
                if hasattr(s, "track_timer"):
                    totals.append(float(s.track_timer.total_seconds or 0.0))
                    renders.append(float(getattr(s.track_timer, "render_seconds", 0.0) or 0.0))
            except Exception:
                pass
        if totals:
            if all(abs(v - totals[0]) < 0.5 for v in totals):
                entry["total"] = totals[0]
            else:
                entry["total"] = sum(v for v in totals if v > 0)
        if renders:
            entry["render"] = max(renders)
        sc = _read_sidecar()
        if sc:
            try:
                if float(sc.get("total_seconds", 0.0) or 0.0) > entry["total"]:
                    entry["total"] = float(sc.get("total_seconds", 0.0))
            except Exception:
                pass
            try:
                if float(sc.get("render_seconds", 0.0) or 0.0) > entry["render"]:
                    entry["render"] = float(sc.get("render_seconds", 0.0))
            except Exception:
                pass
    except Exception:
        pass
    return entry


def _ensure_uid(item) -> str:
    """Stable step identity (old files have no uid). Writes only outside draw."""
    try:
        if not getattr(item, "uid", ""):
            item.uid = uuid.uuid4().hex
        return item.uid
    except Exception:
        return ""


def _get_entry(scene) -> dict:
    """Per-scene step truth, adopting visible values when new (never zeroes)."""
    key = _store_key_for_scene(scene)
    entry = _time_store.get(key)
    if entry is None:
        entry = {"ms": {}}
        _time_store[key] = entry
    try:
        for m in scene.track_timer.milestones:
            uid = _ensure_uid(m)
            if uid and uid not in entry["ms"]:
                entry["ms"][uid] = {
                    "s": float(m.seconds or 0.0),
                    "a": bool(m.active),
                    "d": bool(m.done),
                }
    except Exception:
        pass
    return entry


def _set_float_attr(rna, attr, value, force=False) -> bool:
    """Write a float prop only when its whole second changed. Returns True if written."""
    try:
        cur = float(getattr(rna, attr, 0.0) or 0.0)
        if force or int(cur) != int(value):
            setattr(rna, attr, float(value))
            return True
    except Exception:
        pass
    return False


def _set_bool_attr(rna, attr, value) -> bool:
    try:
        if bool(getattr(rna, attr)) != bool(value):
            setattr(rna, attr, bool(value))
            return True
    except Exception:
        pass
    return False


def _sync_store_to_props(scene, force=False):
    """Push truth (store) to display (props). Cheap: writes only on change."""
    try:
        props = scene.track_timer
    except Exception:
        return
    try:
        fe = _file_state.get(_file_key())
    except Exception:
        fe = None
    if fe is None:
        return
    try:
        _set_float_attr(props, "total_seconds", fe["total"], force)
        _set_float_attr(props, "session_seconds", fe["session"], force)
        _set_float_attr(props, "render_seconds", fe.get("render", 0.0), force)
        _set_bool_attr(props, "running", fe["running"])
        entry = _time_store.get(_store_key_for_scene(scene))
        ms = entry.get("ms", {}) if entry else {}
        for m in props.milestones:
            try:
                uid = getattr(m, "uid", "")
            except Exception:
                continue
            if uid and uid in ms:
                st = ms[uid]
                _set_float_attr(m, "seconds", st["s"], force)
                _set_bool_attr(m, "active", st["a"])
                _set_bool_attr(m, "done", st["d"])
    except Exception:
        pass


def _sync_all_scenes(force=False):
    try:
        for s in bpy.data.scenes:
            try:
                if hasattr(s, "track_timer"):
                    _sync_store_to_props(s, force)
            except Exception:
                pass
    except Exception:
        pass


def _display_state(scene, props):
    """Read-only numbers for drawing (panel/statusbar). Never mutates."""
    total = float(props.total_seconds or 0.0)
    session = float(props.session_seconds or 0.0)
    render = float(getattr(props, "render_seconds", 0.0) or 0.0)
    running = bool(props.running)
    ms_secs, active, done = {}, set(), set()
    try:
        fe = _file_state.get(_file_key())
        if fe is not None:
            total, session, running = fe["total"], fe["session"], fe["running"]
            render = fe.get("render", render)
        entry = _time_store.get(_store_key_for_scene(scene))
        ms = entry.get("ms", {}) if entry else {}
        for m in props.milestones:
            try:
                uid = getattr(m, "uid", "")
            except Exception:
                uid = ""
            if uid and uid in ms:
                st = ms[uid]
                ms_secs[uid] = st["s"]
                if st["a"]:
                    active.add(uid)
                if st["d"]:
                    done.add(uid)
            else:
                try:
                    ms_secs[uid or id(m)] = float(m.seconds or 0.0)
                    if m.active:
                        active.add(uid or id(m))
                    if m.done:
                        done.add(uid or id(m))
                except Exception:
                    pass
    except Exception:
        pass
    return {"total": total, "session": session, "render": render,
            "running": running, "secs": ms_secs,
            "active": active, "done": done}


def _drop_ms_from_store(scene, uids):
    try:
        key = _store_key_for_scene(scene)
        entry = _time_store.get(key)
        if entry is None:
            return
        for u in uids:
            entry["ms"].pop(u, None)
    except Exception:
        pass


def _prune_store_to_current_file():
    """Drop entries from other files (only one .blend open at a time)."""
    try:
        fp = _file_key()
    except Exception:
        return
    try:
        for key in [k for k in _time_store if k[0] != fp]:
            del _time_store[key]
        for key in [k for k in _file_state if k != fp]:
            del _file_state[key]
        for key in [k for k in _paused_files if k != fp]:
            _paused_files.discard(key)
    except Exception:
        pass


def _resolve_scene_for_tick():
    """The same scene the panel shows: 1st window, else 1st scene."""
    try:
        for win in bpy.context.window_manager.windows:
            if getattr(win, "scene", None) is not None:
                return win.scene
    except Exception:
        pass
    try:
        if bpy.data.scenes:
            return bpy.data.scenes[0]
    except Exception:
        pass
    return None


def get_props(context=None):
    scene = None
    if context is not None and hasattr(context, "scene") and context.scene:
        scene = context.scene
    else:
        # fallback quando chamado sem contexto (timer em background)
        if bpy.data.scenes:
            # prefere a cena ativa da primeira janela, senao a primeira
            try:
                for win in bpy.context.window_manager.windows:
                    if win.scene:
                        return win.scene.track_timer
            except Exception:
                pass
            scene = bpy.data.scenes[0]
    if scene is None:
        return None
    return scene.track_timer


def _milestones_snapshot(scene):
    """Step table: names/dates from props, seconds/flags from the store."""
    out = []
    try:
        props = scene.track_timer
        entry = _time_store.get(_store_key_for_scene(scene)) or {}
        ms = entry.get("ms", {})
        for m in props.milestones:
            try:
                uid = getattr(m, "uid", "")
            except Exception:
                uid = ""
            st = ms.get(uid) if uid else None
            sec = st["s"] if st else float(m.seconds or 0.0)
            act = st["a"] if st else bool(m.active)
            done = st["d"] if st else bool(m.done)
            out.append({
                "uid": uid,
                "name": m.name,
                "seconds": float(sec),
                "hms": format_hms(sec),
                "active": bool(act),
                "done": bool(done),
                "created": getattr(m, "created", ""),
                "finished": m.finished,
            })
    except Exception:
        pass
    return out


def _migrate_loose_files():
    """Move legacy loose files (json/csvs/old report) into the reports folder. Once."""
    try:
        fp = bpy.data.filepath
        if not fp:
            return
        d = reports_dir()
        base = _blend_base_name()
        if not d or not base:
            return
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        legacy = [
            fp + ".tracktime.json",
            os.path.join(os.path.dirname(fp), base + ".tracktime.csv"),
            os.path.join(os.path.dirname(fp), base + ".milestones.csv"),
            os.path.splitext(fp)[0] + "_RELATORIO.txt",
        ]
        for old in legacy:
            try:
                if old and os.path.isfile(old):
                    new = os.path.join(d, os.path.basename(old))
                    if os.path.abspath(old) != os.path.abspath(new) and not os.path.exists(new):
                        os.replace(old, new)
            except Exception:
                continue
    except Exception:
        pass


def sidecar_path_for_blend() -> str | None:
    """Machine cache JSON — lives with the other reports (zero loose files)."""
    d = reports_dir()
    base = _blend_base_name()
    if not d or not base:
        return None
    return os.path.join(d, base + ".tracktime.json")


def reports_dir() -> str | None:
    """Pasta de relatorios: <pasta do .blend>/<nome configuravel>."""
    try:
        fp = bpy.data.filepath
    except Exception:
        return None
    if not fp:
        return None
    folder_name = "TIME REPORT"
    try:
        prefs = _addon_prefs()
        if prefs is not None and hasattr(prefs, "report_folder_name"):
            folder_name = getattr(prefs, "report_folder_name") or folder_name
    except Exception:
        pass
    folder_name = (folder_name or "TIME REPORT").strip() or "TIME REPORT"
    for ch in ("/", "\\"):
        folder_name = folder_name.replace(ch, "_")
    return os.path.join(os.path.dirname(fp), folder_name)


def _blend_base_name() -> str | None:
    try:
        fp = bpy.data.filepath
    except Exception:
        return None
    if not fp:
        return None
    return os.path.splitext(os.path.basename(fp))[0]


def milestones_csv_path() -> str | None:
    d = reports_dir()
    base = _blend_base_name()
    if not d or not base:
        return None
    return os.path.join(d, base + ".milestones.csv")


def sessions_csv_path() -> str | None:
    d = reports_dir()
    base = _blend_base_name()
    if not d or not base:
        return None
    return os.path.join(d, base + ".tracktime.csv")


def write_milestones_csv(scene=None):
    """Rewrite .milestones.csv with the current step table (store-based)."""
    try:
        csv_path = milestones_csv_path()
        if not csv_path:
            return
        if scene is None:
            scene = _resolve_scene_for_tick()
        if scene is None:
            return
        try:
            props = scene.track_timer
        except Exception:
            return
        entry = _time_store.get(_store_key_for_scene(scene)) or {}
        ms = entry.get("ms", {})
        parent = os.path.dirname(csv_path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("etapa,segundos,hms,em_andamento,terminada,terminada_em\n")
            for m in props.milestones:
                try:
                    uid = getattr(m, "uid", "")
                except Exception:
                    uid = ""
                st = ms.get(uid) if uid else None
                sec = st["s"] if st else float(m.seconds or 0.0)
                act = st["a"] if st else bool(m.active)
                done = st["d"] if st else bool(m.done)
                name = (m.name or "").replace('"', '""')
                f.write(f'"{name}",{sec:.0f},"{format_hms(sec)}",'
                        f'{"1" if act else "0"},{"1" if done else "0"},"{m.finished}"\n')
    except Exception:
        pass


def rewrite_sessions_csv():
    """Rewrite the sessions CSV from the JSON log (no duplicates)."""
    try:
        data = _read_sidecar()
        if not data:
            return
        hist = data.get("sessions")
        if not isinstance(hist, list):
            return
        csv_path = sessions_csv_path()
        if not csv_path:
            return
        parent = os.path.dirname(csv_path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("inicio,fim,sessao_segundos,sessao_hms,total_segundos,total_hms,blend,recuperada\n")
            for h in hist:
                try:
                    ini = (h.get("start") or "").replace('"', '""')
                    end = (h.get("end") or "").replace('"', '""')
                    ss = float(h.get("session_seconds", 0.0) or 0.0)
                    sh = h.get("session_hms", format_hms(ss))
                    ts = float(h.get("total_seconds", 0.0) or 0.0)
                    th = h.get("total_hms", format_hms(ts))
                    fp = (h.get("blend") or bpy.data.filepath or "").replace('"', '""')
                    rec = "1" if h.get("recovered") else "0"
                    f.write(f'"{ini}","{end}",{ss:.0f},"{sh}",{ts:.0f},"{th}","{fp}",{rec}\n')
                except Exception:
                    continue
    except Exception:
        pass


def _ensure_parent(path) -> bool:
    try:
        parent = os.path.dirname(path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        return True
    except Exception:
        return False


def save_sidecar(scene=None):
    """Crash-proof backup (store-based): totals + open session + steps."""
    try:
        if scene is None:
            scene = _resolve_scene_for_tick()
        if scene is None:
            return
        try:
            props = scene.track_timer
        except Exception:
            return
        path = sidecar_path_for_blend()
        if not path or not _ensure_parent(path):
            return
        fe = _file_entry()
        snap = _milestones_snapshot(scene)
        try:
            sess_start = props.session_start_str or ""
        except Exception:
            sess_start = ""
        data = {
            "blend": bpy.data.filepath,
            "total_seconds": float(fe["total"]),
            "total_hms": format_hms(fe["total"]),
            "render_seconds": float(fe.get("render", 0.0)),
            "last_update": datetime.now().isoformat(timespec="seconds"),
            "open_session": {
                "start": sess_start,
                "session_seconds": float(fe["session"]),
                "total_seconds": float(fe["total"]),
                "updated": _now_str(),
            },
            "milestones": snap,
        }
        old = _read_sidecar() or {}
        data["sessions"] = old.get("sessions") if isinstance(old.get("sessions"), list) else []
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        write_milestones_csv(scene)
    except Exception:
        pass


def _clear_open_session():
    """Zero the open-session marker (after recover/finish/reset)."""
    try:
        path = sidecar_path_for_blend()
        if not path or not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return
        data["open_session"] = {"start": "", "session_seconds": 0.0,
                                "total_seconds": data.get("total_seconds", 0.0),
                                "updated": _now_str()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _recover_open_session():
    """Log the session left open by a close/crash (returns True if recovered)."""
    try:
        data = _read_sidecar()
        if not data:
            return False
        op = data.get("open_session") or {}
        try:
            sess = float(op.get("session_seconds", 0.0) or 0.0)
        except Exception:
            sess = 0.0
        if sess < 1.0:
            return False
        stamp = op.get("updated") or _now_str()
        entry = {
            "start": op.get("start") or "",
            "end": stamp,
            "session_seconds": sess,
            "session_hms": format_hms(sess),
            "total_seconds": float(op.get("total_seconds", sess) or sess),
            "total_hms": format_hms(float(op.get("total_seconds", sess) or sess)),
            "milestones": data.get("milestones", []),
            "recovered": True,
        }
        log = data.get("sessions")
        if not isinstance(log, list):
            log = []
        log.append(entry)
        data["sessions"] = log
        data["last_update"] = datetime.now().isoformat(timespec="seconds")
        path = sidecar_path_for_blend()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        _clear_open_session()
        rewrite_sessions_csv()
        return True
    except Exception:
        return False


def append_session_log(session_seconds, total_seconds, session_start="", scene=None):
    """Log a finished session to the sidecar json + append to the sessions CSV."""
    try:
        path = sidecar_path_for_blend()
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if scene is None:
            scene = _resolve_scene_for_tick()
        snap = _milestones_snapshot(scene) if scene is not None else []
        if not path or not _ensure_parent(path):
            return
        entry = {
            "start": session_start or "",
            "end": stamp,
            "session_seconds": float(session_seconds),
            "session_hms": format_hms(session_seconds),
            "total_seconds": float(total_seconds),
            "total_hms": format_hms(total_seconds),
            "milestones": snap,
        }
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        if not isinstance(data, dict):
            data = {}
        log = data.get("sessions")
        if not isinstance(log, list):
            log = []
        log.append(entry)
        data["sessions"] = log
        data["blend"] = bpy.data.filepath
        data["total_seconds"] = float(total_seconds)
        data["total_hms"] = format_hms(total_seconds)
        data["last_update"] = datetime.now().isoformat(timespec="seconds")
        data["milestones"] = snap
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # single CSV writer: same 8-column format, no duplicates, no drift
        rewrite_sessions_csv()
        write_milestones_csv(scene)
    except Exception:
        pass


# -------------------------------------------------------------------
# Relatorio TXT + pagina de configuracao externa
# -------------------------------------------------------------------

_ADDON_ENABLED = False
_ATEXIT_REGISTERED = False

_REPORT_DEFAULTS = {
    "report_include_header": True,
    "report_include_total": True,
    "report_include_session": True,
    "report_include_session_avg": True,
    "report_include_period": True,
    "report_include_value": True,
    "report_include_milestones": True,
    "report_include_history": True,
    "report_include_settings": False,
    "report_auto_on_save": True,
    "report_auto_on_exit": True,
    "report_suffix": "_REPORT",
    "report_folder_name": "TIME REPORT",
    "report_html": True,
}


def _addon_prefs():
    """Retorna o bloco de preferencias do addon, ou None."""
    try:
        prefs = bpy.context.preferences
        if prefs is None:
            return None
        addons = getattr(prefs, "addons", None)
        if addons is None:
            return None
        for key in (_ADDON_ID, "track_timer_addon", __name__):
            try:
                entry = addons.get(key)
            except Exception:
                entry = None
            if entry is not None:
                return getattr(entry, "preferences", None)
    except Exception:
        pass
    return None


def get_report_opts():
    """Opcoes do relatorio: preferencias do addon, ou padroes se indisponivel."""
    opts = dict(_REPORT_DEFAULTS)
    prefs = _addon_prefs()
    if prefs is not None:
        for k in opts:
            try:
                if hasattr(prefs, k):
                    opts[k] = getattr(prefs, k)
            except Exception:
                pass
    return opts


def report_path_for_blend() -> str | None:
    """Caminho do TXT dentro da pasta de relatorios."""
    d = reports_dir()
    base = _blend_base_name()
    if not d or not base:
        return None
    opts = get_report_opts()
    suffix = (opts.get("report_suffix") or "_REPORT").strip() or "_REPORT"
    return os.path.join(d, base + suffix + ".txt")


def _read_sessions_history():
    try:
        path = sidecar_path_for_blend()
        if not path or not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("sessions"), list):
            return data["sessions"]
    except Exception:
        pass
    return []


def build_report_text(scene, props, opts, reason=""):
    L = []
    add = L.append
    now = _now_str()
    try:
        blend = bpy.data.filepath or "(unsaved)"
    except Exception:
        blend = "(unsaved)"
    try:
        folder = reports_dir() or "—"
    except Exception:
        folder = "—"

    if opts.get("report_include_header"):
        try:
            _cli, _proj = _report_names(scene)
        except Exception:
            _cli, _proj = ("", "")
        if not _proj:
            _proj = os.path.splitext(os.path.basename(blend))[0]
        add("=" * 56)
        add(T("TIME REPORT — TRACK TIMER"))
        add("=" * 56)
        add(f"{T('Project   :')} {_proj}")
        if _cli:
            add(f"{T('Client    :')} {_cli}")
        add(f"{T('Folder    :')} {folder}")
        add(f"{T('Generated :')} {now}" + (f"  {T('(reason: {r})').format(r=T(reason))}" if reason else ""))
        add("")

    if opts.get("report_include_period"):
        add("-" * 56)
        add(T("PERIOD (start-end time)"))
        add("-" * 56)
        add(f"{T('Project start :')} {props.project_start_str or '—'}")
        if props.session_start_str or props.session_seconds > 0:
            add(f"{T('Session start :')} {props.session_start_str or '—'}")
            fim_txt = now + (" " + T("(in progress)") if props.running else "")
            add(f"{T('Session end   :')} {fim_txt}")
        else:
            add(T("Current session : none (click Start)"))
        add("")

    if opts.get("report_include_total"):
        add("-" * 56)
        add(T("HOURS SPENT"))
        add("-" * 56)
        add(f"{T('Total   :')} {format_hms(props.total_seconds)}  "
            f"({props.total_seconds:.0f}s = {props.total_seconds / 3600.0:.2f}h)")
        if opts.get("report_include_session"):
            add(f"{T('Session :')} {format_hms(props.session_seconds)}  ({props.session_seconds:.0f}s)")
        try:
            _r = float(getattr(props, "render_seconds", 0.0) or 0.0)
        except Exception:
            _r = 0.0
        if _r > 0.5:
            add(T("Render: {t}").format(t=format_hms(_r)))
        add("")
    elif opts.get("report_include_session"):
        add("-" * 56)
        add(T("HOURS SPENT"))
        add("-" * 56)
        add(f"{T('Session :')} {format_hms(props.session_seconds)}  ({props.session_seconds:.0f}s)")
        add("")

    if opts.get("report_include_value") and props.hourly_rate > 0:
        valor = props.total_seconds / 3600.0 * props.hourly_rate
        add("-" * 56)
        add(T("VALUE"))
        add("-" * 56)
        add(f"{T('Rate/hour     :')} {_currency_symbol()} {props.hourly_rate:,.2f}")
        add(f"{T('Estimated value :')} {_currency_symbol()} {valor:,.2f}")
        add("")

    if opts.get("report_include_milestones"):
        add("-" * 56)
        add(T("STEPS"))
        add("-" * 56)
        if len(props.milestones) == 0:
            add(T("(no steps created)"))
        else:
            n = 0
            for i, m in enumerate(props.milestones, 1):
                if m.done:
                    st = T("DONE")
                    fim = m.finished or "—"
                elif m.active:
                    st = T("IN PROGRESS")
                    fim = T("now (in progress)")
                elif m.seconds > 0:
                    st = T("PAUSED")
                    fim = "—"
                else:
                    st = T("PENDING")
                    fim = "—"
                add(f"{i:02d}. [{st}] {m.name} — {format_hms(m.seconds)}")
                add(f"     {T('start:')} {m.created or '—'}   {T('end:')} {fim}")
                if m.done:
                    n += 1
            add(T("Summary: {d}/{n} done").format(d=n, n=len(props.milestones)))
        add("")

    if opts.get("report_include_history"):
        add("-" * 56)
        add(T("SESSIONS HISTORY"))
        add("-" * 56)
        hist = _read_sessions_history()
        if not hist:
            add(T("(no finished sessions logged)"))
        else:
            for h in hist:
                ini = h.get("start") or "—"
                rec = (" " + T("(recovered)")) if h.get("recovered") else ""
                add(f"- {ini} -> {h.get('end', '—')}  |  "
                    f"{T('session')} {h.get('session_hms', '?')}  |  {T('total')} {h.get('total_hms', '?')}{rec}")
        add("")

    if opts.get("report_include_settings"):
        add("-" * 56)
        add(T("SETTINGS USED"))
        add("-" * 56)
        add(f"{T('Pause when unfocused :')} {T('YES') if props.pause_on_unfocus else T('NO')}")
        add(f"{T('Pause when idle     :')} {T('YES') if props.pause_on_idle else T('NO')} {T('({m} min)').format(m=props.idle_minutes)}")
        add("")

    add("=" * 56)
    add(T("Generated by the Track Timer addon"))
    add("=" * 56)
    return "\n".join(L) + "\n"


def _html_escape(s) -> str:
    try:
        s = str(s)
    except Exception:
        s = ""
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _report_names(scene=None):
    """(client, project) for the HTML header: scene fields first, prefs as fallback."""
    client, project = "", ""
    try:
        if scene is not None:
            props = scene.track_timer
            client = (getattr(props, "client_name", "") or "").strip()
            project = (getattr(props, "project_name", "") or "").strip()
    except Exception:
        pass
    if not client or not project:
        try:
            prefs = _addon_prefs()
            if prefs is not None:
                if not client:
                    client = (getattr(prefs, "client_name", "") or "").strip()
                if not project:
                    project = (getattr(prefs, "project_name", "") or "").strip()
        except Exception:
            pass
    if not project:
        try:
            project = _blend_base_name() or ""
        except Exception:
            project = ""
    return client, project


def html_report_path() -> str | None:
    d = reports_dir()
    base = _blend_base_name()
    if not d or not base:
        return None
    opts = get_report_opts()
    suffix = (opts.get("report_suffix") or "_REPORT").strip() or "_REPORT"
    return os.path.join(d, base + suffix + ".html")


def build_report_html(scene, props, opts) -> str:
    now = _now_str()
    client, project = _report_names(scene)
    try:
        lang = (get_lang() or "en_US").split("_")[0]
    except Exception:
        lang = "en"
    title = T("TIME REPORT — TRACK TIMER")
    css = ("body{font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;"
           "color:#1f2937;background:#eef1f6;margin:0}"
           ".page{max-width:920px;margin:28px auto;background:#fff;"
           "padding:0 0 32px;border-radius:14px;overflow:hidden;"
           "box-shadow:0 6px 24px rgba(15,23,42,.12)}"
           ".hero{background:linear-gradient(135deg,#111827,#1d4ed8);"
           "color:#fff;padding:28px 36px;"
           "print-color-adjust:exact;-webkit-print-color-adjust:exact}"
           ".hero h1{margin:0;font-size:24px;letter-spacing:.5px}"
           ".hero .sub{opacity:.85;font-size:13px;margin-top:6px}"
           ".meta{display:grid;grid-template-columns:1fr 1fr;gap:10px 28px;"
           "padding:22px 36px 0;font-size:14px}"
           ".meta div{min-width:0;overflow-wrap:anywhere}"
           ".note{padding:0 36px;font-size:14px}"
           "td{overflow-wrap:anywhere}"
           ".meta b{color:#6b7280;font-weight:600;margin-right:6px}"
           "h2{font-size:13px;text-transform:uppercase;letter-spacing:1.5px;"
           "color:#6b7280;padding:0 36px;margin:28px 0 0}"
           ".kpis{display:flex;gap:12px;padding:14px 36px 0;flex-wrap:wrap}"
           ".kpi{flex:1;min-width:150px;background:#f8fafc;"
           "border:1px solid #e5e7eb;border-radius:10px;padding:12px 16px}"
           ".kpi .k{font-size:11px;color:#6b7280;text-transform:uppercase;"
           "letter-spacing:1px}"
           ".kpi .v{font-size:24px;font-weight:700;margin-top:2px}"
           ".kpi .s{font-size:12px;color:#6b7280;margin-top:2px}"
           "table{border-collapse:collapse;width:calc(100% - 72px);"
           "margin:12px 36px 0;font-size:14px}"
           "th,td{border:1px solid #e5e7eb;padding:8px 12px;text-align:left}"
           "th{background:#f1f5f9}tr:nth-child(even) td{background:#f8fafc}"
           ".pill{display:inline-block;padding:2px 10px;border-radius:999px;"
           "font-size:12px;font-weight:700;white-space:nowrap;"
           "print-color-adjust:exact;-webkit-print-color-adjust:exact}"
           ".p-done{background:#dcfce7;color:#166534}"
           ".p-active{background:#dbeafe;color:#1d4ed8}"
           ".p-paused{background:#fef3c7;color:#92400e}"
           ".p-pend{background:#f3f4f6;color:#4b5563}"
           ".progress{height:10px;background:#e5e7eb;border-radius:999px;"
           "margin:12px 36px 0;overflow:hidden}"
           ".progress>div{height:100%;background:linear-gradient(90deg,#2563eb,#60a5fa);"
           "print-color-adjust:exact;-webkit-print-color-adjust:exact}"
           ".sumline{padding:8px 36px 0;font-size:13px;color:#6b7280}"
           ".foot{color:#6b7280;font-size:12px;margin:28px 36px 0}"
           ".printbtn{position:fixed;top:16px;right:16px;padding:10px 18px;"
           "font-size:14px;cursor:pointer;border-radius:8px;"
           "border:1px solid #cbd5e1;background:#fff;"
           "box-shadow:0 2px 6px rgba(0,0,0,.15)}"
           "@media print{.printbtn{display:none}body{background:#fff}"
           ".page{box-shadow:none;margin:0;max-width:none;border-radius:0}}")
    L = []
    L.append('<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8">' % _html_escape(lang))
    L.append("<title>%s — %s</title><style>%s</style></head><body>" % (
        _html_escape(project or "Track Timer"), _html_escape(title), css))
    L.append('<button class="printbtn" onclick="window.print()">%s</button><div class="page">' % _html_escape(T("Print / Save as PDF")))
    L.append('<div class="hero"><h1>%s</h1><div class="sub">%s • %s</div></div>' % (
        _html_escape(title), _html_escape(project or "Track Timer"), _html_escape(now)))
    if opts.get("report_include_header"):
        try:
            folder = reports_dir() or "—"
        except Exception:
            folder = "—"
        L.append('<div class="meta">'
                 '<div><b>%s</b>%s</div>'
                 '<div><b>%s</b>%s</div>'
                 '<div><b>%s</b>%s</div>'
                 '<div><b>%s</b>%s</div></div>' % (
            _html_escape(T("Project:")), _html_escape(project or "—"),
            _html_escape(T("Client:")), _html_escape(client or "—"),
            _html_escape(T("Folder:")), _html_escape(folder),
            _html_escape(T("Generated:")), _html_escape(now)))
    if opts.get("report_include_period"):
        L.append("<h2>%s</h2>" % _html_escape(T("PERIOD (start-end time)")))
        if props.session_start_str or props.session_seconds > 0:
            end_txt = now + (" " + T("(in progress)") if props.running else "")
            L.append("<table><tr><th>%s</th><th>%s</th><th>%s</th></tr>" % (
                _html_escape(T("Project start :")), _html_escape(T("Start time")),
                _html_escape(T("End"))))
            L.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr></table>" % (
                _html_escape(props.project_start_str or "—"),
                _html_escape(props.session_start_str or "—"),
                _html_escape(end_txt)))
        else:
            L.append("<p class=\"note\">%s<br>%s</p>" % (
                _html_escape(T("Project start :") + " " + (props.project_start_str or "—")),
                _html_escape(T("Current session : none (click Start)"))))
    _show_hours = opts.get("report_include_total") or opts.get("report_include_session")
    _show_value = opts.get("report_include_value") and props.hourly_rate > 0
    if _show_hours or _show_value:
        L.append("<h2>%s</h2>" % _html_escape(T("HOURS SPENT")))
        L.append('<div class="kpis">')
        if opts.get("report_include_total"):
            L.append('<div class="kpi"><div class="k">%s</div><div class="v">%s</div>'
                     '<div class="s">%.2f h</div></div>' % (
                _html_escape(T("Total")), _html_escape(format_hms(props.total_seconds)),
                props.total_seconds / 3600.0))
        if opts.get("report_include_session_avg", True):
            try:
                _avg, _n = _session_average()
            except Exception:
                _avg, _n = (0.0, 0)
            L.append('<div class="kpi"><div class="k">%s</div><div class="v">%s</div>'
                     '<div class="s">%s</div></div>' % (
                _html_escape(T("Avg session")), _html_escape(format_hms(_avg)),
                _html_escape(T("avg of {n} sessions").format(n=_n))))
        try:
            _r = float(getattr(props, "render_seconds", 0.0) or 0.0)
        except Exception:
            _r = 0.0
        if opts.get("report_include_total") and _r > 0.5:
            L.append('<div class="kpi"><div class="k">%s</div><div class="v">%s</div></div>' % (
                _html_escape(T("Render")), _html_escape(format_hms(_r))))
        if _show_value:
            valor = props.total_seconds / 3600.0 * props.hourly_rate
            cur = _currency_symbol()
            L.append('<div class="kpi"><div class="k">%s</div><div class="v">%s %.2f</div>'
                     '<div class="s">%s %.2f/h</div></div>' % (
                _html_escape(T("Estimated value")), _html_escape(cur), valor,
                _html_escape(cur), props.hourly_rate))
        L.append("</div>")
    if opts.get("report_include_milestones"):
        L.append("<h2>%s</h2>" % _html_escape(T("STEPS")))
        if len(props.milestones) == 0:
            L.append("<p class=\"note\">%s</p>" % _html_escape(T("(no steps created)")))
        else:
            _nn = len(props.milestones)
            _dn = 0
            try:
                _dn = sum(1 for _mm in props.milestones if _mm.done)
            except Exception:
                pass
            _pct = int(round(100.0 * _dn / _nn)) if _nn else 0
            L.append('<div class="progress"><div style="width:%d%%"></div></div>' % _pct)
            L.append("<table><tr><th>#</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>" % (
                _html_escape(T("Step")), _html_escape(T("Status")),
                _html_escape(T("Time")), _html_escape(T("Start time")),
                _html_escape(T("End"))))
            n = 0
            for i, m in enumerate(props.milestones, 1):
                if m.done:
                    st, fim, pcls = T("DONE"), m.finished or "—", "p-done"
                elif m.active:
                    st, fim, pcls = T("IN PROGRESS"), T("now (in progress)"), "p-active"
                elif m.seconds > 0:
                    st, fim, pcls = T("PAUSED"), "—", "p-paused"
                else:
                    st, fim, pcls = T("PENDING"), "—", "p-pend"
                L.append("<tr><td>%d</td><td>%s</td><td><span class=\"pill %s\">%s</span></td>"
                         "<td>%s</td><td>%s</td><td>%s</td></tr>" % (
                    i, _html_escape(m.name), pcls, _html_escape(st),
                    _html_escape(format_hms(m.seconds)),
                    _html_escape(m.created or "—"), _html_escape(fim)))
                if m.done:
                    n += 1
            L.append("</table><p class=\"sumline\">%s</p>" % _html_escape(
                T("Summary: {d}/{n} done").format(d=n, n=len(props.milestones))))
    if opts.get("report_include_history"):
        L.append("<h2>%s</h2>" % _html_escape(T("SESSIONS HISTORY")))
        hist = _read_sessions_history()
        if not hist:
            L.append("<p class=\"note\">%s</p>" % _html_escape(T("(no finished sessions logged)")))
        else:
            L.append("<table><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>" % (
                _html_escape(T("Start time")), _html_escape(T("End")),
                _html_escape(T("Session")), _html_escape(T("Total"))))
            for h in hist:
                rec = (" " + T("(recovered)")) if h.get("recovered") else ""
                L.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s%s</td></tr>" % (
                    _html_escape(h.get("start") or "—"),
                    _html_escape(h.get("end") or "—"),
                    _html_escape(h.get("session_hms", "?")),
                    _html_escape(h.get("total_hms", "?")), _html_escape(rec)))
            L.append("</table>")
    if opts.get("report_include_settings"):
        L.append("<h2>%s</h2>" % _html_escape(T("SETTINGS USED")))
        L.append("<p class=\"note\">%s %s<br>%s %s %s</p>" % (
            _html_escape(T("Pause when unfocused :")),
            _html_escape(T("YES") if props.pause_on_unfocus else T("NO")),
            _html_escape(T("Pause when idle     :")),
            _html_escape(T("YES") if props.pause_on_idle else T("NO")),
            _html_escape(T("({m} min)").format(m=props.idle_minutes))))
    L.append('<p class="foot">%s</p></div></body></html>' % _html_escape(
        T("Generated by the Track Timer addon")))
    return "\n".join(L) + "\n"


def generate_report(reason=""):
    """Gera/atualiza o TXT na pasta do .blend. Retorna o caminho ou None."""
    try:
        path = report_path_for_blend()
        if not path:
            return None
        props = get_props()
        if props is None:
            return None
        try:
            _gscene = _resolve_scene_for_tick()
        except Exception:
            _gscene = None
        try:
            _sync_store_to_props(_gscene, force=True)
        except Exception:
            pass
        opts = get_report_opts()
        text = build_report_text(_gscene, props, opts, reason)
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            props.last_report_path = path
        except Exception:
            pass
        if opts.get("report_html", True):
            try:
                hpath = html_report_path()
                if hpath:
                    hfolder = os.path.dirname(hpath)
                    if hfolder and not os.path.exists(hfolder):
                        os.makedirs(hfolder, exist_ok=True)
                    with open(hpath, "w", encoding="utf-8") as f:
                        try:
                            _hscene = _resolve_scene_for_tick()
                        except Exception:
                            _hscene = None
                        f.write(build_report_html(_hscene, props, opts))
            except Exception:
                pass
        return path
    except Exception:
        return None


def auto_report_if_enabled(context=None, reason=""):
    """Gera o relatorio se a opcao automatica correspondente estiver ligada."""
    try:
        opts = get_report_opts()
    except Exception:
        return None
    key = "report_auto_on_exit" if reason == "exit" else "report_auto_on_save"
    if not opts.get(key):
        return None
    try:
        if not bpy.data.filepath:
            return None
    except Exception:
        return None
    return generate_report(reason=reason)


@bpy.app.handlers.persistent
def _on_save_post(dummy):
    # save_pre already synced truth into the file; here only the report
    auto_report_if_enabled(reason="save")


@bpy.app.handlers.persistent
def _on_load_pre(dummy):
    # gera o relatorio do projeto ANTIGO antes de trocar de arquivo
    try:
        if bpy.data.filepath:
            auto_report_if_enabled(reason="project switch")
    except Exception:
        pass


def _on_blender_exit():
    # best effort: flush truth to disk so nothing is lost on quit.
    # (Even if this never runs, the open session is recovered on load.)
    if not _ADDON_ENABLED:
        return
    try:
        _sync_all_scenes(force=True)
    except Exception:
        pass
    try:
        save_sidecar()
    except Exception:
        pass
    try:
        auto_report_if_enabled(reason="exit")
    except Exception:
        pass


def _resolve_milestone_index(props, idx: int) -> int:
    """idx < 0 significa 'usar o selecionado na lista'."""
    try:
        if idx is None or idx < 0:
            idx = props.milestones_index
        if 0 <= idx < len(props.milestones):
            return idx
    except Exception:
        pass
    return -1


def _parallel_mode() -> str:
    try:
        prefs = _addon_prefs()
        if prefs is not None and getattr(prefs, "parallel_mode", "parallel") == "split":
            return "split"
    except Exception:
        pass
    return "parallel"


def _focus_grace() -> float:
    try:
        prefs = _addon_prefs()
        if prefs is not None:
            return max(0.0, min(30.0, float(getattr(prefs, "focus_grace", 3) or 0)))
    except Exception:
        pass
    return 3.0


# -------------------------------------------------------------------
# Viewport overlay (always-visible clock)
# -------------------------------------------------------------------

_overlay_handle = None


def _overlay_wanted() -> bool:
    try:
        prefs = _addon_prefs()
        if prefs is not None:
            return bool(getattr(prefs, "show_overlay", True))
    except Exception:
        pass
    return True


def _overlay_draw():
    # store-only read: never touch context/props from a draw callback
    try:
        import blf
    except Exception:
        return
    try:
        try:
            st = _file_state.get(_file_key())
        except Exception:
            st = None
        if st:
            label = format_hms(st.get("total", 0.0))
            if st.get("running"):
                label += "  REC"
        else:
            label = "--:--:--"
        font_id = 0
        blf.size(font_id, 22, 72)
        try:
            blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.9)
        except Exception:
            pass
        blf.color(font_id, 1.0, 1.0, 1.0, 0.9)
        blf.position(font_id, 24, 44, 0)
        blf.draw(font_id, label)
    except Exception:
        pass


def _overlay_sync():
    """Match the viewport handler to the preference (add once, remove cleanly)."""
    global _overlay_handle
    try:
        want = _overlay_wanted()
    except Exception:
        want = True
    try:
        if want and _overlay_handle is None:
            _overlay_handle = bpy.types.SpaceView3D.draw_handler_add(
                _overlay_draw, (), "WINDOW", "POST_PIXEL")
        elif not want and _overlay_handle is not None:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(_overlay_handle, "WINDOW")
            except Exception:
                pass
            _overlay_handle = None
    except Exception:
        pass


def _overlay_remove():
    global _overlay_handle
    try:
        if _overlay_handle is not None:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(_overlay_handle, "WINDOW")
            except Exception:
                pass
            _overlay_handle = None
    except Exception:
        pass


def _request_redraw():
    """Redraw only sidebars (UI regions) and the status bar — not viewports."""
    try:
        for win in bpy.context.window_manager.windows:
            try:
                for area in win.screen.areas:
                    try:
                        if area.type == "VIEW_3D":
                            try:
                                overlay_on = _overlay_wanted()
                            except Exception:
                                overlay_on = True
                            try:
                                for region in area.regions:
                                    try:
                                        if region.type == "UI":
                                            region.tag_redraw()
                                        elif overlay_on and region.type == "WINDOW":
                                            region.tag_redraw()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        elif area.type == "STATUSBAR":
                            area.tag_redraw()
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass


def _any_job_running() -> bool:
    """True while Blender runs a render/bake/composite job (UI blocked = work)."""
    try:
        fn = getattr(bpy.app, "is_job_running", None)
        if fn is None:
            return False
        for jt in ("RENDER", "COMPOSITE", "OBJECT_BAKE", "OBJECT_BAKE_TEXTURE"):
            try:
                if fn(jt):
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False


# -------------------------------------------------------------------
# Recent foreground apps (picker source + live display)
# -------------------------------------------------------------------

_recent_apps = []  # [{exe, title, last}] most-recent-first, Blender excluded
_MAX_RECENT = 25
_last_fg = None  # (exe, title, is_self) for the panel line
_last_fg_sig = None


def _note_fg_app(pid, exe, title):
    try:
        if pid is None or pid == 0:
            return
        try:
            if int(pid) == int(os.getpid()):
                return  # Blender itself is not interesting here
        except Exception:
            pass
        exe = (exe or "").strip()
        title = (title or "").strip()
        if not exe and not title:
            return
        key = (exe.lower(), title.lower())
        nowm = time.monotonic()
        for r in _recent_apps:
            if (r["exe"].lower(), r["title"].lower()) == key:
                r["last"] = nowm
                if title and not r["title"]:
                    r["title"] = title
                _recent_apps.sort(key=lambda r: r["last"], reverse=True)
                return
        _recent_apps.insert(0, {"exe": exe, "title": title, "last": nowm})
        del _recent_apps[_MAX_RECENT:]
    except Exception:
        pass


def _app_suggestions(filter_text="", limit=8):
    """Recent apps not yet allowed, filtered by typed text (exe or title)."""
    try:
        f = _norm_app(filter_text)
    except Exception:
        f = ""
    try:
        allowed = set(_allowed_apps_list())
    except Exception:
        allowed = set()
    out = []
    try:
        for r in _recent_apps:
            exe = (r.get("exe") or "").strip()
            if not exe:
                continue
            if _norm_app(exe) in allowed:
                continue
            if f and f not in _norm_app(exe) and f not in _norm_app(r.get("title") or ""):
                continue
            out.append({"exe": exe, "title": (r.get("title") or "").strip()})
            if len(out) >= limit:
                break
    except Exception:
        pass
    return out


def _fg_display_text() -> str:
    """Panel line. Pure formatting of the tick cache (safe in draw)."""
    try:
        info = _last_fg
    except Exception:
        info = None
    if not info:
        return T("Focused: {x}").format(x=T("unknown"))
    exe, title, is_self = info
    if is_self:
        return T("Focused: {x}").format(x=T("Blender (this window)"))
    base = exe or T("unknown")
    if title:
        base += " — " + (title if len(title) <= 48 else title[:47] + "…")
    return T("Focused: {x}").format(x=base)


def track_timer_tick():
    """Called every 1s via bpy.app.timers.

    Must never raise: Blender would silently cancel the timer and the
    count/list would freeze forever.
    """
    global _last_tick_mono, _last_sidecar_save, _last_props_sync, _last_drawn_int, _unfocused_since, _last_fg, _last_fg_sig
    try:
        nowm = time.monotonic()
        if _last_tick_mono is None:
            _last_tick_mono = nowm
            return 1.0
        delta = nowm - _last_tick_mono
        _last_tick_mono = nowm

        if delta < 0:
            return 1.0
        if _render_active or _any_job_running():
            # blocked UI (render/bake) is real work: credit the elapsed time
            if delta > 86400.0:
                delta = 86400.0
        elif delta > 5.0:
            # sleep/hibernate/lag must not inject fake hours
            delta = 5.0

        # foreground window every tick (display + allowlist + recents)
        try:
            _fgpid, _fgname, _fgtitle = fg_info()
        except Exception:
            _fgpid, _fgname, _fgtitle = (None, None, None)
        try:
            _fg_self = bool(_fgpid) and str(_fgpid) == str(os.getpid())
        except Exception:
            _fg_self = False
        try:
            _note_fg_app(_fgpid, _fgname, _fgtitle)
        except Exception:
            pass
        try:
            _sig = (_fgpid, _fgname)
            if _sig != _last_fg_sig:
                _last_fg_sig = _sig
                _last_fg = ((_fgname or ""), (_fgtitle or ""), _fg_self)
                _request_redraw()
        except Exception:
            pass

        scene = _resolve_scene_for_tick()
        if scene is None:
            return 1.0
        try:
            props = scene.track_timer
        except Exception:
            return 1.0

        fe = _file_entry()
        entry = _get_entry(scene)

        # enforce undo-proof flags (store -> props, write on change only)
        try:
            if bool(props.running) != bool(fe["running"]):
                props.running = bool(fe["running"])
        except Exception:
            pass
        try:
            ms = entry.get("ms", {})
            for m in props.milestones:
                try:
                    uid = getattr(m, "uid", "")
                except Exception:
                    continue
                if uid and uid in ms:
                    st = ms[uid]
                    try:
                        if bool(m.active) != bool(st["a"]):
                            m.active = bool(st["a"])
                    except Exception:
                        pass
                    try:
                        if bool(m.done) != bool(st["d"]):
                            m.done = bool(st["d"])
                    except Exception:
                        pass
        except Exception:
            pass

        counting = False
        if fe["running"]:
            paused_reason = ""
            eff_focused = True
            # 1) lost focus? (minimized, other window/app, Alt+Tab)
            if props.pause_on_unfocus:
                pid, pname, ptitle = _fgpid, _fgname, _fgtitle
                if pid is not None and not (pid != 0 and str(pid) == str(os.getpid())):
                    try:
                        allowed = fg_matches_allowed(pname, ptitle)
                    except Exception:
                        allowed = False
                    if allowed:
                        _unfocused_since = None
                    else:
                        if _unfocused_since is None:
                            _unfocused_since = nowm
                        if (nowm - _unfocused_since) > _focus_grace():
                            eff_focused = False
                else:
                    _unfocused_since = None
                if not eff_focused:
                    paused_reason = T("PAUSED — Blender unfocused")
            # 2) idle? (coffee break with Blender still in front)
            if eff_focused and not paused_reason and props.pause_on_idle:
                idle = get_idle_seconds()
                limit = max(1, int(props.idle_minutes)) * 60.0
                if idle >= limit:
                    paused_reason = T("PAUSED — idle for {m}min").format(m=int(idle // 60))

            try:
                if props.paused_reason != paused_reason:
                    props.paused_reason = paused_reason
            except Exception:
                pass

            if not paused_reason:
                counting = True
                fe["total"] += delta
                fe["session"] += delta
                # active steps across ALL scenes (file-level billing)
                try:
                    active_steps = []
                    for s in bpy.data.scenes:
                        try:
                            if not hasattr(s, "track_timer"):
                                continue
                            e = _get_entry(s)
                            for m in s.track_timer.milestones:
                                try:
                                    uid = getattr(m, "uid", "")
                                except Exception:
                                    continue
                                if uid and uid in e["ms"]:
                                    st = e["ms"][uid]
                                    if st["a"] and not st["d"]:
                                        active_steps.append((e, uid))
                        except Exception:
                            continue
                    if active_steps:
                        if _parallel_mode() == "split":
                            share = delta / len(active_steps)
                            for e, uid in active_steps:
                                e["ms"][uid]["s"] += share
                        else:
                            for e, uid in active_steps:
                                e["ms"][uid]["s"] += delta
                except Exception:
                    pass
        else:
            try:
                if props.paused_reason != "":
                    props.paused_reason = ""
            except Exception:
                pass

        # redraw only when the visible state flips (not every tick)
        try:
            cur_int = int(fe["total"])
        except Exception:
            cur_int = -1
        marker = ("run", cur_int) if counting else ("stop", cur_int)
        if marker != _last_drawn_int:
            _last_drawn_int = marker
            _request_redraw()
        try:
            _overlay_sync()
        except Exception:
            pass

        # light props sync (~20 s) + sidecar backup (~30 s, store-based)
        if props.autosave_sidecar and (nowm - _last_sidecar_save > 30.0):
            _last_sidecar_save = nowm
            _sync_store_to_props(scene)
            save_sidecar(scene)
        elif nowm - _last_props_sync > 20.0:
            _last_props_sync = nowm
            _sync_store_to_props(scene)

        return 1.0
    except Exception:
        # never kill the timer
        return 1.0


# -------------------------------------------------------------------
# Properties
# -------------------------------------------------------------------

class TrackTimerMilestone(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Step", default="New step")
    uid: bpy.props.StringProperty(
        name="ID",
        default="",
        description="Stable step identity (internal: protects time against Ctrl+Z)",
    )
    active: bpy.props.BoolProperty(
        name="In progress",
        description="Marked = you are working on THIS step right now. You can mark several at the same time",
        default=False,
    )
    done: bpy.props.BoolProperty(
        name="Done",
        description="Marked = finished step, frozen time",
        default=False,
    )
    seconds: bpy.props.FloatProperty(name="Seconds", default=0.0)
    created: bpy.props.StringProperty(name="Created at", default="")
    finished: bpy.props.StringProperty(name="Finished at", default="")


class TrackTimerProps(bpy.types.PropertyGroup):
    running: bpy.props.BoolProperty(name="Counting", default=False)
    total_seconds: bpy.props.FloatProperty(name="Total (s)", default=0.0)
    session_seconds: bpy.props.FloatProperty(name="Session (s)", default=0.0)
    render_seconds: bpy.props.FloatProperty(name="Render (s)", default=0.0)
    paused_reason: bpy.props.StringProperty(name="Pause reason", default="")
    pause_on_unfocus: bpy.props.BoolProperty(
        name="Pause when Blender loses focus",
        description="If on: minimized, switched window/app or watching a video = pause. If off: it counts straight until you pause/finish",
        default=True,
    )
    pause_on_idle: bpy.props.BoolProperty(
        name="Pause when idle",
        description="Pauses even with Blender in front if there is no keyboard/mouse for X minutes (coffee break). Windows only.",
        default=True,
    )
    idle_minutes: bpy.props.IntProperty(
        name="Idle (min)",
        description="Minutes without keyboard/mouse to count as idle",
        default=5, min=1, max=120,
    )
    hourly_rate: bpy.props.FloatProperty(
        name="Rate / hour",
        description="Optional: to estimate the job value",
        default=0.0, min=0.0,
    )
    show_in_statusbar: bpy.props.BoolProperty(
        name="Show in status bar",
        default=True,
    )
    autosave_sidecar: bpy.props.BoolProperty(
        name="Auto backup next to the .blend",
        description="Saves .tracktime.json next to the .blend every 30s and on finish, so no time is lost if you close without saving",
        default=True,
    )
    milestones: bpy.props.CollectionProperty(type=TrackTimerMilestone)
    milestones_index: bpy.props.IntProperty(name="Selected step", default=0)
    session_start_str: bpy.props.StringProperty(
        name="Session started at", default="",
        description="Time the current session started (used in the report)",
    )
    client_name: bpy.props.StringProperty(name="Client", default="")
    project_name: bpy.props.StringProperty(name="Project", default="")
    project_start_str: bpy.props.StringProperty(
        name="Project started at", default="",
        description="Time work on this file started (used in the report)",
    )
    last_report_path: bpy.props.StringProperty(
        name="Last report", default="",
        description="Path of the last generated TXT report",
    )


# -------------------------------------------------------------------
# Operators (timer global)
# -------------------------------------------------------------------

class TRACKTIMER_OT_start(bpy.types.Operator):
    bl_idname = "tracktimer.start"
    bl_label = "Start"
    bl_description = "Start / resume counting"
    _label_key = "Start"
    _desc_key = "Start / resume counting"

    def execute(self, context):
        global _last_tick_mono
        p = context.scene.track_timer
        fe = _file_entry()
        fe["running"] = True
        if not p.session_start_str:
            p.session_start_str = _now_str()
        if not p.project_start_str:
            p.project_start_str = _now_str()
        _last_tick_mono = time.monotonic()
        _sync_all_scenes()
        self.report({"INFO"}, T("Track Timer: counting started"))
        return {"FINISHED"}


class TRACKTIMER_OT_pause(bpy.types.Operator):
    bl_idname = "tracktimer.pause"
    bl_label = "Pause"
    bl_description = "Pause counting (keeps the total)"
    _label_key = "Pause"
    _desc_key = "Pause counting (keeps the total)"

    def execute(self, context):
        p = context.scene.track_timer
        try:
            fe = _file_entry()
            was_running = bool(fe["running"])
            fe["running"] = False
            if was_running:
                _paused_files.add(_file_key())
        except Exception:
            pass
        _sync_all_scenes()
        if p.autosave_sidecar:
            save_sidecar(context.scene)
        self.report({"INFO"}, T("Track Timer: paused"))
        return {"FINISHED"}


class TRACKTIMER_OT_finish(bpy.types.Operator):
    bl_idname = "tracktimer.finish"
    bl_label = "Finish session"
    bl_description = "Stop counting and log the session to the .csv/.json in the reports folder"
    _label_key = "Finish session"
    _desc_key = "Stop counting and log the session to the .csv/.json in the reports folder"

    def execute(self, context):
        p = context.scene.track_timer
        fe = _file_entry()
        was_running = bool(fe["running"])
        sess0 = float(fe.get("session", 0.0))
        fe["running"] = False
        if was_running or sess0 > 0:
            try:
                _paused_files.add(_file_key())
            except Exception:
                pass
        _sync_all_scenes()
        sess, tot = float(fe["session"]), float(fe["total"])
        append_session_log(sess, tot, p.session_start_str, context.scene)
        fe["session"] = 0.0
        p.session_start_str = ""
        save_sidecar(context.scene)
        _sync_all_scenes()
        self.report({"INFO"}, T("Track Timer: session of {s} logged. Total: {t}").format(s=format_hms(sess), t=format_hms(tot)))
        auto_report_if_enabled(context, reason="session finished")
        return {"FINISHED"}


class TRACKTIMER_OT_reset_total(bpy.types.Operator):
    bl_idname = "tracktimer.reset_total"
    bl_label = "Reset total"
    bl_description = "Reset total and session (to start a new model). Does NOT delete steps (use Clear steps for that)"
    _label_key = "Reset total"
    _desc_key = "Reset total and session (to start a new model). Does NOT delete steps (use Clear steps for that)"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        p = context.scene.track_timer
        fe = _file_entry()
        fe["running"] = False
        fe["total"] = 0.0
        fe["session"] = 0.0
        try:
            _paused_files.discard(_file_key())
        except Exception:
            pass
        p.session_start_str = ""
        p.project_start_str = ""
        save_sidecar(context.scene)
        _sync_all_scenes()
        self.report({"INFO"}, T("Track Timer: total reset (steps kept)"))
        return {"FINISHED"}


class TRACKTIMER_OT_add_minutes(bpy.types.Operator):
    bl_idname = "tracktimer.add_minutes"
    bl_label = "Adjust time"
    bl_description = "Manual adjustment (e.g. forgot to start, or counted non-work time)"
    _label_key = "Adjust time"
    _desc_key = "Manual adjustment (e.g. forgot to start, or counted non-work time)"
    minutes: bpy.props.FloatProperty(name="Minutes (+/-)", default=5.0)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "minutes", text=T("Minutes (+/-)"))

    def execute(self, context):
        try:
            fe = _file_entry()
            fe["total"] = max(0.0, fe["total"] + self.minutes * 60.0)
            _sync_all_scenes()
            tot = float(fe["total"])
        except Exception:
            p = context.scene.track_timer
            tot = max(0.0, float(p.total_seconds or 0.0) + self.minutes * 60.0)
            try:
                p.total_seconds = tot
            except Exception:
                pass
        self.report({"INFO"}, T("Track Timer: total adjusted to {t}").format(t=format_hms(tot)))
        return {"FINISHED"}


class TRACKTIMER_OT_export_csv(bpy.types.Operator):
    bl_idname = "tracktimer.export_csv"
    bl_label = "Export CSV"
    bl_description = "Update the .tracktime.csv and .milestones.csv in the reports folder"
    _label_key = "Export CSV"
    _desc_key = "Update the .tracktime.csv and .milestones.csv in the reports folder"

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({"ERROR"}, T("Save the .blend first (reports live in its folder)"))
            return {"CANCELLED"}
        rewrite_sessions_csv()
        write_milestones_csv(context.scene)
        self.report({"INFO"}, T("Track Timer: CSVs updated in the reports folder"))
        return {"FINISHED"}


# -------------------------------------------------------------------
# Pagina de configuracao externa (Preferences) + relatorio
# -------------------------------------------------------------------

class TrackTimerPreferences(bpy.types.AddonPreferences):
    bl_idname = _ADDON_ID

    language: bpy.props.EnumProperty(
        name="Language",
        description="Addon language (English US is the default)",
        items=LANGUAGES,
        default="en_US",
        update=_update_language,
    )
    report_folder_name: bpy.props.StringProperty(
        name="Reports folder name",
        description="Folder created next to the .blend to hold the TXT report and CSVs",
        default="TIME REPORT",
    )
    report_include_header: bpy.props.BoolProperty(
        name="Header (project, folder, date)",
        default=True,
    )
    report_include_total: bpy.props.BoolProperty(
        name="Hours spent (total)",
        default=True,
    )
    report_include_session: bpy.props.BoolProperty(
        name="Current session hours",
        default=True,
    )
    report_include_session_avg: bpy.props.BoolProperty(
        name="Average session",
        description="Show the average session time in the report (from all logged sessions)",
        default=True,
    )
    report_include_period: bpy.props.BoolProperty(
        name="Period (start-end time)",
        description="Shows project start, session start and end",
        default=True,
    )
    report_include_value: bpy.props.BoolProperty(
        name="Estimated value",
        default=True,
    )
    report_include_milestones: bpy.props.BoolProperty(
        name="Steps table",
        description="Lists each step with status, time, start and end",
        default=True,
    )
    report_include_history: bpy.props.BoolProperty(
        name="Sessions history",
        default=True,
    )
    report_include_settings: bpy.props.BoolProperty(
        name="Settings used",
        default=False,
    )
    report_auto_on_save: bpy.props.BoolProperty(
        name="Generate/update on save and session finish",
        description="Updates the TXT in the reports folder whenever you save the .blend or finish a session",
        default=True,
    )
    report_auto_on_exit: bpy.props.BoolProperty(
        name="Generate when Blender closes",
        description="Tries to update the TXT when quitting Blender (via exit auto-save)",
        default=True,
    )
    report_suffix: bpy.props.StringProperty(
        name="File suffix",
        description="E.g. _REPORT creates 'mymodel_REPORT.txt' in the reports folder",
        default="_REPORT",
    )
    auto_start_on_first_use: bpy.props.BoolProperty(
        name="Start on first edit or save",
        description="Start counting on the first real scene change or save after opening (unless paused or finished)",
        default=True,
    )
    allowed_apps: bpy.props.StringProperty(
        name="Allowed apps (e.g. PureRef, Photoshop)",
        description="Comma-separated names. When one of these apps is focused, it still counts as work",
        default="PureRef",
    )
    app_pick: bpy.props.StringProperty(
        name="Type to filter",
        description="Type part of the app or window name to filter suggestions below",
        default="",
    )
    focus_grace: bpy.props.IntProperty(
        name="Focus grace (s)",
        description="Seconds of lost focus tolerated before pausing (quick Alt+Tab)",
        default=3, min=0, max=30,
    )
    parallel_mode: bpy.props.EnumProperty(
        name="Step time mode",
        description="How time is shared when several steps are active at once",
        items=(
            ("parallel", "Count in parallel",
             "Each active step gets the full time (their sum may exceed the total)"),
            ("split", "Split between active steps",
             "The elapsed time is divided equally between active steps"),
        ),
        default="parallel",
    )
    step_autostart: bpy.props.BoolProperty(
        name="Step auto-start",
        description="Automatically start step 1 on new outlines and advance to the next step on finish",
        default=True,
    )
    currency: bpy.props.StringProperty(
        name="Currency symbol",
        description="Optional symbol (empty = automatic per language)",
        default="",
    )
    client_name: bpy.props.StringProperty(
        name="Client name",
        description="Shown in the HTML report header",
        default="",
    )
    project_name: bpy.props.StringProperty(
        name="Project name",
        description="Shown in the HTML report header (empty = .blend name)",
        default="",
    )
    default_template: bpy.props.EnumProperty(
        name="Example outline",
        description="Which step outline the example button creates",
        items=(
            ("general", "General", ""),
            ("animation", "Animation", ""),
            ("archviz", "Archviz", ""),
            ("motion", "Motion", ""),
        ),
        default="general",
    )
    report_html: bpy.props.BoolProperty(
        name="Also generate HTML report",
        description="Write a printable HTML version next to the TXT on every report",
        default=True,
    )
    show_overlay: bpy.props.BoolProperty(
        name="Show timer overlay in viewport",
        description="Always-visible clock in the 3D viewport (may cost redraws in heavy scenes)",
        default=True,
    )
    show_day_week: bpy.props.BoolProperty(
        name="Show today / week",
        description="Show today's and this week's hours in the panel",
        default=True,
    )
    show_client_header: bpy.props.BoolProperty(
        name="Show client header",
        description="Show the client/project fields at the top of the panel (fill in first)",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "language", text=T("Language"))
        layout.prop(self, "report_folder_name", text=T("Reports folder name"))
        try:
            folder = reports_dir() or "—"
        except Exception:
            folder = "—"
        layout.label(text=T("What goes into the TXT report ({folder}):").format(folder=folder), icon="TEXT")
        col = layout.column(align=True)
        col.prop(self, "report_include_header", text=T("Header (project, folder, date)"))
        col.prop(self, "report_include_total", text=T("Hours spent (total)"))
        col.prop(self, "report_include_session", text=T("Current session hours"))
        col.prop(self, "report_include_session_avg", text=T("Average session"))
        col.prop(self, "report_include_period", text=T("Period (start-end time)"))
        col.prop(self, "report_include_value", text=T("Estimated value"))
        col.prop(self, "report_include_milestones", text=T("Steps table"))
        col.prop(self, "report_include_history", text=T("Sessions history"))
        col.prop(self, "report_include_settings", text=T("Settings used"))
        layout.separator()
        layout.label(text=T("Automatic:"), icon="TIME")
        col2 = layout.column(align=True)
        col2.prop(self, "report_auto_on_save", text=T("Generate/update on save and session finish"))
        col2.prop(self, "report_auto_on_exit", text=T("Generate when Blender closes"))
        col2.prop(self, "report_suffix", text=T("File suffix"))
        layout.separator()
        layout.prop(self, "auto_start_on_first_use", text=T("Start on first edit or save"))
        layout.label(text=T("Work apps (counted as work even when focused):"), icon="INFO")
        try:
            _cur = [x.strip() for x in (self.allowed_apps or "").split(",") if x.strip()]
        except Exception:
            _cur = []
        if _cur:
            for _a in _cur:
                _row = layout.row(align=True)
                _row.label(text=_a, icon="CHECKMARK")
                _op = _row.operator("tracktimer.app_remove", text="", icon="X", emboss=False)
                _op.name = _a
        else:
            layout.label(text=T("(none — only Blender counts)"))
        _row2 = layout.row(align=True)
        _row2.prop(self, "app_pick", text=T("Type to filter:"))
        _row2.operator("tracktimer.app_add_current", icon="ADD", text="")
        try:
            _sugs = _app_suggestions(getattr(self, "app_pick", "") or "")
        except Exception:
            _sugs = []
        for _sg in _sugs:
            _r = layout.row(align=True)
            _op = _r.operator("tracktimer.app_add", text=_sg["exe"], icon="ADD")
            _op.name = _sg["exe"]
            if _sg.get("title"):
                _t = _sg["title"]
                _r.label(text=(_t if len(_t) <= 40 else _t[:39] + "…"))
        _typed = (getattr(self, "app_pick", "") or "").strip()
        if _typed and not any(_norm_app(_typed) == _norm_app(_a) for _a in _cur):
            _op3 = layout.operator("tracktimer.app_add", text=T("Add \"{x}\"").format(x=_typed), icon="ADD")
            _op3.name = _typed
        layout.prop(self, "focus_grace", text=T("Focus grace (s)"))
        layout.label(text=T("Step time mode") + ":")
        rowm = layout.row(align=True)
        rowm.prop_enum(self, "parallel_mode", "parallel", text=T("Count in parallel"))
        rowm.prop_enum(self, "parallel_mode", "split", text=T("Split between active steps"))
        layout.prop(self, "step_autostart", text=T("Step auto-start"))
        layout.prop(self, "currency", text=T("Currency symbol"))
        layout.separator()
        layout.label(text=T("Extras:"), icon="PRESET")
        col3 = layout.column(align=True)
        col3.prop(self, "client_name", text=T("Client name"))
        col3.prop(self, "project_name", text=T("Project name"))
        col3.prop(self, "report_html", text=T("Also generate HTML report"))
        col3.prop(self, "show_overlay", text=T("Show timer overlay in viewport"))
        col3.prop(self, "show_day_week", text=T("Show today / week"))
        col3.prop(self, "show_client_header", text=T("Show client header"))
        layout.label(text=T("Example outline") + ":")
        rowt = layout.row(align=True)
        rowt.prop_enum(self, "default_template", "general", text=T("General"))
        rowt.prop_enum(self, "default_template", "animation", text=T("Animation"))
        rowt.prop_enum(self, "default_template", "archviz", text=T("Archviz"))
        rowt.prop_enum(self, "default_template", "motion", text=T("Motion"))


class TRACKTIMER_OT_report_generate(bpy.types.Operator):
    bl_idname = "tracktimer.report_generate"
    bl_label = "Generate report now"
    bl_description = "Generate the TXT report in the reports folder, with the content chosen on the settings page"
    _label_key = "Generate report now"
    _desc_key = "Generate the TXT report in the reports folder, with the content chosen on the settings page"

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({"ERROR"}, T("Save the .blend first (the report lives in its folder)"))
            return {"CANCELLED"}
        path = generate_report(reason="manual")
        if path:
            self.report({"INFO"}, T("Report saved: {p}").format(p=path))
            return {"FINISHED"}
        self.report({"ERROR"}, T("Could not generate the report"))
        return {"CANCELLED"}


class TRACKTIMER_OT_report_open_folder(bpy.types.Operator):
    bl_idname = "tracktimer.report_open_folder"
    bl_label = "Open reports folder"
    bl_description = "Open the folder with the TXT report and CSVs"
    _label_key = "Open reports folder"
    _desc_key = "Open the folder with the TXT report and CSVs"

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({"ERROR"}, T("Save the .blend first (the report lives in its folder)"))
            return {"CANCELLED"}
        folder = reports_dir() or os.path.dirname(bpy.data.filepath)
        try:
            bpy.ops.wm.path_open(filepath=folder)
        except Exception:
            try:
                if _IS_WINDOWS:
                    os.startfile(folder)  # noqa: S606 -- pasta local do proprio projeto
                else:
                    self.report({"WARNING"}, T("Folder: {f}").format(f=folder))
                    return {"FINISHED"}
            except Exception:
                self.report({"WARNING"}, T("Folder: {f}").format(f=folder))
                return {"FINISHED"}
        return {"FINISHED"}


class TRACKTIMER_OT_report_html(bpy.types.Operator):
    bl_idname = "tracktimer.report_html"
    bl_label = "Generate HTML report"
    bl_description = "Generate a printable HTML report (open in a browser, print to PDF)"
    _label_key = "Generate HTML report"
    _desc_key = "Generate a printable HTML report (open in a browser, print to PDF)"

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({"ERROR"}, T("Save the .blend first (the report lives in its folder)"))
            return {"CANCELLED"}
        try:
            scene = context.scene
            _sync_store_to_props(scene, force=True)
            props = scene.track_timer
        except Exception:
            self.report({"ERROR"}, T("Could not generate the report"))
            return {"CANCELLED"}
        try:
            path = html_report_path()
            if not path:
                self.report({"ERROR"}, T("Could not generate the report"))
                return {"CANCELLED"}
            folder = os.path.dirname(path)
            if folder and not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(build_report_html(context.scene, props, get_report_opts()))
        except Exception:
            self.report({"ERROR"}, T("Could not generate the report"))
            return {"CANCELLED"}
        self.report({"INFO"}, T("Report saved: {p}").format(p=path))
        return {"FINISHED"}


class TRACKTIMER_OT_app_add(bpy.types.Operator):
    bl_idname = "tracktimer.app_add"
    bl_label = "Allow app"
    bl_description = "Add this app to the allowed list (counts as work when focused)"
    _label_key = "Allow app"
    _desc_key = "Add this app to the allowed list (counts as work when focused)"
    name: bpy.props.StringProperty(name="App", default="")

    def execute(self, context):
        try:
            prefs = _addon_prefs()
        except Exception:
            prefs = None
        if prefs is None:
            self.report({"ERROR"}, T("Preferences unavailable"))
            return {"CANCELLED"}
        new = (self.name or "").strip()
        if not new:
            return {"CANCELLED"}
        try:
            cur = [x.strip() for x in (getattr(prefs, "allowed_apps", "") or "").split(",") if x.strip()]
        except Exception:
            cur = []
        if _norm_app(new) not in [_norm_app(c) for c in cur]:
            cur.append(new)
            try:
                prefs.allowed_apps = ", ".join(cur)
            except Exception:
                pass
        self.report({"INFO"}, T("'{n}' will now count as work").format(n=new))
        return {"FINISHED"}


class TRACKTIMER_OT_app_remove(bpy.types.Operator):
    bl_idname = "tracktimer.app_remove"
    bl_label = "Remove app"
    bl_description = "Remove this app from the allowed list"
    _label_key = "Remove app"
    _desc_key = "Remove this app from the allowed list"
    name: bpy.props.StringProperty(name="App", default="")

    def execute(self, context):
        try:
            prefs = _addon_prefs()
            if prefs is None:
                return {"CANCELLED"}
        except Exception:
            return {"CANCELLED"}
        target = _norm_app(self.name)
        try:
            cur = [x.strip() for x in (getattr(prefs, "allowed_apps", "") or "").split(",") if x.strip()]
        except Exception:
            cur = []
        kept = [c for c in cur if _norm_app(c) != target]
        try:
            prefs.allowed_apps = ", ".join(kept)
        except Exception:
            pass
        self.report({"INFO"}, T("'{n}' removed from allowed").format(n=(self.name or "").strip()))
        return {"FINISHED"}


class TRACKTIMER_OT_app_add_current(bpy.types.Operator):
    bl_idname = "tracktimer.app_add_current"
    bl_label = "Add focused app"
    bl_description = "Add the last app seen in focus (switch to it first if the list is empty)"
    _label_key = "Add focused app"
    _desc_key = "Add the last app seen in focus (switch to it first if the list is empty)"

    def execute(self, context):
        exe = ""
        try:
            for r in _recent_apps:
                cand = (r.get("exe") or "").strip()
                if cand:
                    exe = cand
                    break
        except Exception:
            exe = ""
        if not exe:
            try:
                _pid, _pn, _pt = fg_info()
                if _pn and _pn.strip():
                    try:
                        if not _pid or str(_pid) != str(os.getpid()):
                            exe = _pn.strip()
                    except Exception:
                        exe = _pn.strip()
            except Exception:
                pass
        if not exe:
            self.report({"WARNING"}, T("No other app seen yet — switch to it first"))
            return {"CANCELLED"}
        self.name = exe
        return TRACKTIMER_OT_app_add.execute(self, context)


# -------------------------------------------------------------------
# Operators (milestones)
# -------------------------------------------------------------------

class TRACKTIMER_OT_milestone_add(bpy.types.Operator):
    bl_idname = "tracktimer.milestone_add"
    bl_label = "Add step"
    bl_description = "Add a step (you can add before or during counting)"
    _label_key = "Add step"
    _desc_key = "Add a step (you can add before or during counting)"
    name: bpy.props.StringProperty(name="Step name", default="")
    start_now: bpy.props.BoolProperty(
        name="Start now",
        description="If on, the step is born marked as 'in progress' (you can mark several at the same time)",
        default=True,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "name", text=T("Step name"))
        self.layout.prop(self, "start_now", text=T("Start now"))

    def execute(self, context):
        global _last_tick_mono
        p = context.scene.track_timer
        item = p.milestones.add()
        base = (self.name or "").strip() or T("Step {n}").format(n=len(p.milestones))
        item.name = base
        item.uid = uuid.uuid4().hex
        item.seconds = 0.0
        item.done = False
        item.finished = ""
        item.created = _now_str()
        item.active = bool(self.start_now)
        try:
            _get_entry(context.scene)["ms"][item.uid] = {
                "s": 0.0, "a": bool(self.start_now), "d": False}
        except Exception:
            pass
        p.milestones_index = len(p.milestones) - 1
        if item.active:
            fe = _file_entry()
            if not fe["running"]:
                fe["running"] = True
                if not p.session_start_str:
                    p.session_start_str = _now_str()
                if not p.project_start_str:
                    p.project_start_str = _now_str()
                _last_tick_mono = time.monotonic()
        _sync_all_scenes()
        self.report({"INFO"}, T("Step '{n}' added").format(n=item.name))
        return {"FINISHED"}


class TRACKTIMER_OT_milestone_remove(bpy.types.Operator):
    bl_idname = "tracktimer.milestone_remove"
    bl_label = "Remove step"
    bl_description = "Remove the selected step"
    _label_key = "Remove step"
    _desc_key = "Remove the selected step"
    bl_options = {"REGISTER", "UNDO"}
    index: bpy.props.IntProperty(default=-1)

    def execute(self, context):
        p = context.scene.track_timer
        idx = _resolve_milestone_index(p, self.index)
        if idx < 0:
            self.report({"WARNING"}, T("No step selected"))
            return {"CANCELLED"}
        removed = p.milestones[idx].name
        try:
            uid = getattr(p.milestones[idx], "uid", "")
            if uid:
                _drop_ms_from_store(context.scene, [uid])
        except Exception:
            pass
        p.milestones.remove(idx)
        p.milestones_index = max(0, min(idx, len(p.milestones) - 1))
        self.report({"INFO"}, T("Step '{n}' removed").format(n=removed))
        return {"FINISHED"}


class TRACKTIMER_OT_milestone_toggle_active(bpy.types.Operator):
    bl_idname = "tracktimer.milestone_toggle_active"
    bl_label = "Start / Pause step"
    bl_description = "Mark/unmark 'I'm working on this right now'. You can keep SEVERAL active at the same time. If the global timer is stopped, it starts by itself"
    _label_key = "Start / Pause step"
    _desc_key = "Mark/unmark 'I'm working on this right now'. You can keep SEVERAL active at the same time. If the global timer is stopped, it starts by itself"
    index: bpy.props.IntProperty(default=-1)

    def execute(self, context):
        global _last_tick_mono
        p = context.scene.track_timer
        idx = _resolve_milestone_index(p, self.index)
        if idx < 0:
            self.report({"WARNING"}, T("No step selected"))
            return {"CANCELLED"}
        m = p.milestones[idx]
        try:
            uid = _ensure_uid(m)
            entry = _get_entry(context.scene)
            st = entry["ms"].get(uid)
            if st is None:
                st = {"s": float(m.seconds or 0.0),
                      "a": bool(m.active), "d": bool(m.done)}
                entry["ms"][uid] = st
        except Exception:
            uid, entry, st = "", None, None
        if st is not None and st["d"]:
            self.report({"WARNING"}, T("'{n}' already finished — reopen it to continue").format(n=m.name))
            return {"CANCELLED"}
        new_active = not (st["a"] if st is not None else bool(m.active))
        if st is not None:
            st["a"] = new_active
        else:
            try:
                m.active = new_active
            except Exception:
                pass
        if new_active:
            fe = _file_entry()
            if not fe["running"]:
                fe["running"] = True
                if not p.session_start_str:
                    p.session_start_str = _now_str()
                if not p.project_start_str:
                    p.project_start_str = _now_str()
                _last_tick_mono = time.monotonic()
                _sync_all_scenes()
                self.report({"INFO"}, T("'{n}' in progress (timer started)").format(n=m.name))
                return {"FINISHED"}
            _sync_all_scenes()
            self.report({"INFO"}, T("'{n}' in progress").format(n=m.name))
        else:
            _sync_all_scenes()
            try:
                sec = st["s"] if st is not None else float(m.seconds or 0.0)
            except Exception:
                sec = 0.0
            self.report({"INFO"}, T("'{n}' paused (kept time: {t})").format(n=m.name, t=format_hms(sec)))
        return {"FINISHED"}


class TRACKTIMER_OT_milestone_toggle_done(bpy.types.Operator):
    bl_idname = "tracktimer.milestone_toggle_done"
    bl_label = "Done! / Reopen"
    bl_description = "Mark the step as DONE (freezes its time) or reopen a finished step"
    _label_key = "Done! / Reopen"
    _desc_key = "Mark the step as DONE (freezes its time) or reopen a finished step"
    index: bpy.props.IntProperty(default=-1)

    def invoke(self, context, event):
        # finishing a step that never counted is usually a mistake:
        # ask first instead of silently freezing 00:00
        try:
            p = context.scene.track_timer
            idx = _resolve_milestone_index(p, self.index)
            if idx >= 0:
                m = p.milestones[idx]
                sec = None
                try:
                    entry = _get_entry(context.scene)
                    uid = getattr(m, "uid", "")
                    if uid and uid in entry.get("ms", {}):
                        sec = entry["ms"][uid]["s"]
                except Exception:
                    sec = None
                if sec is None:
                    try:
                        sec = float(m.seconds or 0.0)
                    except Exception:
                        sec = 0.0
                if not bool(m.done) and sec < 1.0:
                    return context.window_manager.invoke_confirm(self, event)
        except Exception:
            pass
        return self.execute(context)

    def execute(self, context):
        p = context.scene.track_timer
        idx = _resolve_milestone_index(p, self.index)
        if idx < 0:
            self.report({"WARNING"}, T("No step selected"))
            return {"CANCELLED"}
        m = p.milestones[idx]
        try:
            uid = _ensure_uid(m)
            entry = _get_entry(context.scene)
            st = entry["ms"].get(uid)
            if st is None:
                st = {"s": float(m.seconds or 0.0),
                      "a": bool(m.active), "d": bool(m.done)}
                entry["ms"][uid] = st
            new_done = not st["d"]
            st["d"] = new_done
            if new_done:
                st["a"] = False
            sec = st["s"]
        except Exception:
            new_done = not bool(m.done)
            try:
                m.done = new_done
                if new_done:
                    m.active = False
            except Exception:
                pass
            try:
                sec = float(m.seconds or 0.0)
            except Exception:
                sec = 0.0
        _sync_all_scenes()
        if new_done:
            m.finished = _now_str()
            self.report({"INFO"}, T("'{n}' DONE in {t}").format(n=m.name, t=format_hms(sec)))
            if p.autosave_sidecar:
                save_sidecar(context.scene)
            # auto-advance (if enabled): the next unfinished step starts right away
            if _pref_bool("step_autostart", True):
                try:
                    entry2 = _get_entry(context.scene)
                    ms2 = entry2.get("ms", {})
                    for _m in p.milestones:
                        try:
                            _u = getattr(_m, "uid", "")
                        except Exception:
                            _u = ""
                        if _u and _u in ms2 and not ms2[_u]["d"]:
                            ms2[_u]["a"] = True
                            break
                    _sync_all_scenes()
                except Exception:
                    pass
        else:
            m.finished = ""
            self.report({"INFO"}, T("'{n}' reopened").format(n=m.name))
        return {"FINISHED"}


class TRACKTIMER_OT_milestone_move(bpy.types.Operator):
    bl_idname = "tracktimer.milestone_move"
    bl_label = "Move step"
    bl_description = "Move the step up/down in the list"
    _label_key = "Move step"
    _desc_key = "Move the step up/down in the list"
    direction: bpy.props.IntProperty(default=-1)  # -1 sobe, +1 desce

    def execute(self, context):
        p = context.scene.track_timer
        idx = p.milestones_index
        if not (0 <= idx < len(p.milestones)):
            return {"CANCELLED"}
        new_idx = idx + self.direction
        if not (0 <= new_idx < len(p.milestones)):
            return {"CANCELLED"}
        p.milestones.move(idx, new_idx)
        p.milestones_index = new_idx
        return {"FINISHED"}


class TRACKTIMER_OT_milestone_clear_finished(bpy.types.Operator):
    bl_idname = "tracktimer.milestone_clear_finished"
    bl_label = "Clear finished"
    bl_description = "Remove all finished steps from the list (keeps the open ones)"
    _label_key = "Clear finished"
    _desc_key = "Remove all finished steps from the list (keeps the open ones)"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        p = context.scene.track_timer
        done_uids = []
        for i in range(len(p.milestones) - 1, -1, -1):
            if p.milestones[i].done:
                try:
                    u = getattr(p.milestones[i], "uid", "")
                    if u:
                        done_uids.append(u)
                except Exception:
                    pass
                p.milestones.remove(i)
        _drop_ms_from_store(context.scene, done_uids)
        p.milestones_index = max(0, min(p.milestones_index, len(p.milestones) - 1))
        return {"FINISHED"}


class TRACKTIMER_OT_milestone_template(bpy.types.Operator):
    bl_idname = "tracktimer.milestone_template"
    bl_label = "Load example outline"
    bl_description = "Add example steps (Blocking, Modeling, UV, Texturing...) — skips ones that already exist"
    _label_key = "Load example outline"
    _desc_key = "Add example steps (Blocking, Modeling, UV, Texturing...) — skips ones that already exist"

    def execute(self, context):
        global _last_tick_mono
        p = context.scene.track_timer
        kind = _template_kind()
        preset = [T(x) if x not in ("UV", "RENDER") else x
                  for x in TEMPLATE_OUTLINES.get(kind, TEMPLATE_OUTLINES["general"])]
        existing = { (m.name or "").strip().upper() for m in p.milestones }
        had_steps = len(p.milestones) > 0
        first_uid = None
        added = 0
        for name in preset:
            if name.upper() not in existing:
                item = p.milestones.add()
                item.name = name
                item.uid = uuid.uuid4().hex
                item.seconds = 0.0
                item.active = False
                item.done = False
                item.created = _now_str()
                item.finished = ""
                existing.add(name.upper())
                if first_uid is None:
                    first_uid = item.uid
                added += 1
        if added:
            p.milestones_index = 0
            if not had_steps and first_uid and _pref_bool("step_autostart", True):
                # fresh outline: step 1 starts working right away
                try:
                    _get_entry(context.scene)["ms"][first_uid]["a"] = True
                except Exception:
                    pass
                try:
                    fe = _file_entry()
                    if not fe["running"]:
                        fe["running"] = True
                        if not p.session_start_str:
                            p.session_start_str = _now_str()
                        if not p.project_start_str:
                            p.project_start_str = _now_str()
                        _last_tick_mono = time.monotonic()
                except Exception:
                    pass
                _sync_all_scenes()
        self.report({"INFO"}, T("{n} example steps added").format(n=added) if added else T("Outline already exists"))
        return {"FINISHED"}


# -------------------------------------------------------------------
# Step outlines per area (animation / archviz / motion / general)
# -------------------------------------------------------------------

TEMPLATE_OUTLINES = {
    "general": ["BLOCKING", "DETAILED MODELING", "RETOPOLOGY", "UV",
                "TEXTURING", "LIGHTING", "RENDER", "POST / DELIVERY"],
    "animation": ["REFERENCES", "BLOCKING", "SPLINE", "POLISH",
                  "PLAYBLAST", "FINAL RENDER", "DELIVERY"],
    "archviz": ["REFERENCES", "BLOCKING", "MODELING", "MATERIALS",
                "LIGHTING", "RENDER", "POST / DELIVERY"],
    "motion": ["STORYBOARD", "STYLEFRAMES", "ANIMATION",
               "COMPOSITING", "RENDER", "DELIVERY"],
}


def _template_kind() -> str:
    try:
        prefs = _addon_prefs()
        if prefs is not None:
            k = getattr(prefs, "default_template", "general")
            if k in TEMPLATE_OUTLINES:
                return k
    except Exception:
        pass
    return "general"


class TRACKTIMER_OT_milestone_add_minutes(bpy.types.Operator):
    bl_idname = "tracktimer.milestone_add_minutes"
    bl_label = "Adjust step"
    bl_description = "Manual time adjustment of the selected step"
    _label_key = "Adjust step"
    _desc_key = "Manual time adjustment of the selected step"
    minutes: bpy.props.FloatProperty(name="Minutes (+/-)", default=5.0)
    index: bpy.props.IntProperty(default=-1)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "minutes", text=T("Minutes (+/-)"))

    def execute(self, context):
        p = context.scene.track_timer
        idx = _resolve_milestone_index(p, self.index)
        if idx < 0:
            self.report({"WARNING"}, T("No step selected"))
            return {"CANCELLED"}
        m = p.milestones[idx]
        try:
            uid = _ensure_uid(m)
            entry = _get_entry(context.scene)
            entry["ms"][uid] = max(0.0, entry["ms"].get(uid, float(m.seconds or 0.0)) + self.minutes * 60.0)
            _sync_store_to_props(context.scene)
        except Exception:
            m.seconds = max(0.0, m.seconds + self.minutes * 60.0)
        self.report({"INFO"}, T("'{n}' adjusted to {t}").format(n=m.name, t=format_hms(m.seconds)))
        return {"FINISHED"}


# -------------------------------------------------------------------
# UI
# -------------------------------------------------------------------

def _currency_symbol() -> str:
    try:
        prefs = _addon_prefs()
        if prefs is not None:
            custom = (getattr(prefs, "currency", "") or "").strip()
            if custom:
                return custom
    except Exception:
        pass
    sym = T("currency_symbol")
    return sym if sym != "currency_symbol" else "$"


class TRACKTIMER_UL_milestones(bpy.types.UIList):
    bl_idname = "TRACKTIMER_UL_milestones"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            # botao comecar/pausar (pode ter varios ativos!)
            if item.done:
                row.label(text="", icon="CHECKMARK")
            else:
                op = row.operator(
                    "tracktimer.milestone_toggle_active", text="",
                    icon="PAUSE" if item.active else "PLAY",
                    emboss=False,
                )
                op.index = index
            # nome editavel direto na lista
            row.prop(item, "name", text="", emboss=False)
            # tempo da etapa (lido do store: exato mesmo com undo/props antigas)
            try:
                _e = _time_store.get(_store_key_for_scene(context.scene)) or {}
                _st = (_e.get("ms", {}) or {}).get(getattr(item, "uid", "") or "", None)
                _sec = _st["s"] if _st else float(item.seconds or 0.0)
            except Exception:
                _sec = float(item.seconds or 0.0)
            row.label(text=format_hms(_sec))
            # botao terminei/reabrir
            op2 = row.operator(
                "tracktimer.milestone_toggle_done", text="",
                icon="CHECKBOX_HLT" if item.done else "CHECKBOX_DEHLT",
                emboss=False,
            )
            op2.index = index
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="")


def _pref_bool(name, default=True) -> bool:
    try:
        prefs = _addon_prefs()
        if prefs is not None and hasattr(prefs, name):
            return bool(getattr(prefs, name))
    except Exception:
        pass
    return default


def _session_average():
    """(avg_seconds, n_sessions) across logged sessions + the open one."""
    total, n = 0.0, 0
    try:
        for h in _read_sessions_history():
            try:
                total += float(h.get("session_seconds", 0.0) or 0.0)
                n += 1
            except Exception:
                continue
        try:
            fe = _file_state.get(_file_key())
            cur = float(fe.get("session", 0.0)) if fe else 0.0
        except Exception:
            cur = 0.0
        if cur > 0:
            total += cur
            n += 1
    except Exception:
        pass
    return ((total / n) if n else 0.0, n)


def _day_week_seconds():
    """(today, this_week) in seconds: history + current open session."""
    try:
        from datetime import date as _date, timedelta as _td, datetime as _dt
        today = _date.today()
        monday = today - _td(days=today.weekday())
    except Exception:
        return (0.0, 0.0)
    ttd, wtd = 0.0, 0.0
    try:
        for h in _read_sessions_history():
            try:
                ds = ((h.get("start") or h.get("end")) or "")[:10]
                d = _dt.strptime(ds, "%Y-%m-%d").date()
                ss = float(h.get("session_seconds", 0.0) or 0.0)
            except Exception:
                continue
            if d == today:
                ttd += ss
            if d >= monday:
                wtd += ss
        try:
            fe = _file_state.get(_file_key())
            if fe and float(fe.get("session", 0.0)) > 0:
                ttd += float(fe["session"])
                wtd += float(fe["session"])
        except Exception:
            pass
    except Exception:
        pass
    return (ttd, wtd)


class TRACKTIMER_PT_panel(bpy.types.Panel):
    bl_label = "Track Timer"
    bl_idname = "TRACKTIMER_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Track Timer"

    def draw(self, context):
        layout = self.layout
        p = context.scene.track_timer
        st8 = _display_state(context.scene, p)

        if _pref_bool("show_client_header", True):
            hbox = layout.box()
            hbox.label(text=T("Client / Project"), icon="INFO")
            hbox.prop(p, "client_name", text=T("Client"))
            hbox.prop(p, "project_name", text=T("Project"))

        # status
        if st8["running"]:
            if p.paused_reason:
                layout.label(text=p.paused_reason, icon="PAUSE")
            else:
                layout.label(text=T("COUNTING..."), icon="TIME")
        else:
            layout.label(text=T("STOPPED"), icon="TIME")

        box = layout.box()
        box.label(text=T("Total: {t}").format(t=format_hms(st8["total"])))
        box.label(text=T("Session: {t}").format(t=format_hms(st8["session"])))
        if _pref_bool("show_day_week", True):
            try:
                _td, _wd = _day_week_seconds()
            except Exception:
                _td, _wd = (0.0, 0.0)
            box.label(text=T("Today: {t}").format(t=format_hms(_td)))
            box.label(text=T("This week: {t}").format(t=format_hms(_wd)))
        if st8["render"] > 0.5:
            box.label(text=T("Render: {t}").format(t=format_hms(st8["render"])), icon="RENDER_ANIMATION")
        if p.hourly_rate > 0:
            valor = st8["total"] / 3600.0 * p.hourly_rate
            box.label(text=f"{T('Est. value:')} {_currency_symbol()} {valor:,.2f}")

        row = layout.row(align=True)
        if not p.running:
            row.operator("tracktimer.start", icon="PLAY")
        else:
            row.operator("tracktimer.pause", icon="PAUSE")
        row.operator("tracktimer.finish", icon="CHECKMARK")

        layout.separator()

        # ---------- STEPS ----------
        mbox = layout.box()
        n_total = len(p.milestones)
        n_active = len(st8["active"] - st8["done"])
        n_done = len(st8["done"])
        mbox.label(text=T("Steps  •  {a} in progress  •  {d}/{n} done").format(a=n_active, d=n_done, n=n_total), icon="CHECKMARK")

        row = mbox.row()
        row.template_list(
            "TRACKTIMER_UL_milestones", "", p, "milestones",
            p, "milestones_index", rows=5,
        )
        col = row.column(align=True)
        col.operator("tracktimer.milestone_add", icon="ADD", text="")
        op_rm = col.operator("tracktimer.milestone_remove", icon="REMOVE", text="")
        op_rm.index = -1
        op_up = col.operator("tracktimer.milestone_move", icon="TRIA_UP", text="")
        op_up.direction = -1
        op_dn = col.operator("tracktimer.milestone_move", icon="TRIA_DOWN", text="")
        op_dn.direction = 1

        if n_total > 0 and 0 <= p.milestones_index < n_total:
            sel = p.milestones[p.milestones_index]
            try:
                sel_uid = getattr(sel, "uid", "")
            except Exception:
                sel_uid = ""
            if sel_uid and sel_uid in st8["secs"]:
                sel_sec = st8["secs"][sel_uid]
                sel_done = sel_uid in st8["done"]
                sel_act = (sel_uid in st8["active"]) and not sel_done
            else:
                sel_sec, sel_act, sel_done = sel.seconds, sel.active, sel.done
            mbox.label(text=T("Selected: {n} — {t}").format(n=sel.name, t=format_hms(sel_sec))
                            + (T("  [DONE]") if sel_done else (T("  [WORKING NOW]") if sel_act else "")))
            r2 = mbox.row(align=True)
            op_a = r2.operator(
                "tracktimer.milestone_toggle_active",
                text=T("Pause step") if sel_act else T("Start step"),
                icon="PAUSE" if sel_act else "PLAY",
            )
            op_a.index = p.milestones_index
            op_d = r2.operator(
                "tracktimer.milestone_toggle_done",
                text=T("Reopen") if sel_done else T("DONE!"),
                icon="X" if sel_done else "CHECKMARK",
            )
            op_d.index = p.milestones_index
            r3 = mbox.row(align=True)
            op_adj = r3.operator("tracktimer.milestone_add_minutes", icon="TIME")
            op_adj.index = p.milestones_index
            op_clr = r3.operator("tracktimer.milestone_clear_finished", icon="TRASH")
        else:
            mbox.label(text=T("No steps. Add BLOCKING, etc."))

        r4 = mbox.row(align=True)
        r4.operator("tracktimer.milestone_add", icon="ADD")
        r4.operator("tracktimer.milestone_template", icon="PRESET")

        try:
            _pprefs = _addon_prefs()
        except Exception:
            _pprefs = None
        if _pprefs is not None:
            mbox.prop(_pprefs, "step_autostart", text=T("Step auto-start"))

        if not st8["running"] and n_active > 0:
            mbox.label(text=T("Global timer stopped: active steps don't count."), icon="INFO")

        layout.separator()
        layout.prop(p, "pause_on_unfocus", text=T("Pause when Blender loses focus"))
        layout.prop(p, "pause_on_idle", text=T("Pause when idle"))
        row = layout.row()
        row.enabled = p.pause_on_idle
        row.prop(p, "idle_minutes", text=T("Idle (min)"))
        layout.prop(p, "hourly_rate", text=T("Rate / hour"))
        layout.prop(p, "show_in_statusbar", text=T("Show in status bar"))
        layout.prop(p, "autosave_sidecar", text=T("Auto backup next to the .blend"))

        layout.separator()
        row = layout.row(align=True)
        row.operator("tracktimer.add_minutes", icon="ADD")
        row.operator("tracktimer.reset_total", icon="TRASH")

        layout.separator()
        rbox = layout.box()
        rbox.label(text=T("TXT report (reports folder)"), icon="TEXT")
        rrow = rbox.row(align=True)
        rrow.operator("tracktimer.report_generate", icon="TEXT")
        rrow.operator("tracktimer.report_open_folder", icon="FILE_FOLDER")
        rbox.operator("tracktimer.report_html", icon="URL")
        rbox.operator("tracktimer.export_csv", icon="EXPORT")
        if p.last_report_path:
            rbox.label(text=T("Last: {f}").format(f=os.path.basename(p.last_report_path)), icon="INFO")
        else:
            rbox.label(text=T("Content in Preferences > Add-ons > Track Timer"), icon="INFO")

        try:
            layout.label(text=_fg_display_text(), icon="INFO")
        except Exception:
            pass
        if _IS_LINUX and (_BACKEND.get("focus") is None or _BACKEND.get("idle") is None):
            layout.label(text=T("Tip: install xdotool and xprintidle for focus + idle detection"), icon="INFO")
        if not bpy.data.filepath:
            layout.label(text=T("Save the .blend to enable .json/.csv backup"), icon="INFO")


def draw_statusbar(self, context):
    try:
        scene = getattr(context, "scene", None)
        if not scene or not hasattr(scene, "track_timer"):
            return
        p = scene.track_timer
        if not p.show_in_statusbar:
            return
        st8 = _display_state(scene, p)
        base = format_hms(st8["total"])
        if st8["running"] and not p.paused_reason:
            act = [u for u in st8["active"] if u not in st8["done"]]
            if len(act) == 1:
                uid = next(iter(act))
                nm, sec = None, None
                try:
                    for m in p.milestones:
                        try:
                            if getattr(m, "uid", "") == uid:
                                nm, sec = m.name, st8["secs"].get(uid, 0.0)
                                break
                        except Exception:
                            continue
                except Exception:
                    pass
                if nm is None:
                    txt = base
                else:
                    txt = f"{base} • {nm} {format_hms(sec)}"
            elif len(act) > 1:
                txt = f"{base} • " + T("{n} steps").format(n=len(act))
            else:
                txt = base
            self.layout.label(text=txt, icon="TIME")
        elif st8["running"]:
            self.layout.label(text=base, icon="PAUSE")
        else:
            self.layout.label(text=base, icon="TIME")
    except Exception:
        pass


# -------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------

@bpy.app.handlers.persistent
def _on_save_pre(dummy):
    global _last_tick_mono
    # sync truth into the .blend BEFORE it is written to disk
    try:
        _sync_all_scenes(force=True)
    except Exception:
        pass
    # saving also starts the clock (unless paused/finished on purpose),
    # so saving first thing still can't lose work time
    try:
        prefs = _addon_prefs()
        if prefs is None:
            first_use_on = True
        else:
            first_use_on = bool(getattr(prefs, "auto_start_on_first_use", True))
    except Exception:
        first_use_on = True
    if not first_use_on:
        return
    try:
        if _file_key() in _paused_files:
            return
        fe = _file_entry()
        if fe["running"]:
            return
        scene = _resolve_scene_for_tick()
        if scene is None:
            return
        p = scene.track_timer
        fe["running"] = True
        _last_tick_mono = time.monotonic()
        if not p.session_start_str:
            p.session_start_str = _now_str()
        if not p.project_start_str:
            p.project_start_str = _now_str()
        _sync_all_scenes()
    except Exception:
        pass


@bpy.app.handlers.persistent
def _on_depsgraph_update(*_args):
    """Start on first REAL work after opening: data changes only.

    Works on fresh AND history files (opening never starts by itself).
    Clicks that merely select, splash dismissal and viewport evaluation
    carry no geometry/transform/shading flags, so they are ignored.
    Stays away after an explicit pause/finish. Cheap: instant return
    once running or paused. Never writes depsgraph data, cannot loop.
    """
    try:
        try:
            prefs = _addon_prefs()
            if prefs is None:
                first_use_on = True
            else:
                first_use_on = bool(getattr(prefs, "auto_start_on_first_use", True))
        except Exception:
            first_use_on = True
        if not first_use_on:
            return
        try:
            fe = _file_entry()
        except Exception:
            return
        try:
            if _file_key() in _paused_files:
                return
            if fe["running"]:
                return
        except Exception:
            return
        # only REAL data changes start the clock: new objects, transforms,
        # sculpt/mesh edits, shading changes. Selection clicks, splash
        # dismissal and viewport evaluation have none of these flags set.
        # Without a verifiable change we stay stopped (never count blank).
        try:
            _dg = None
            for _a in _args:
                if hasattr(_a, "updates"):
                    _dg = _a
                    break
            _real_change = False
            if _dg is not None:
                for _u in _dg.updates:
                    try:
                        if (_u.is_updated_geometry or _u.is_updated_transform
                                or _u.is_updated_shading):
                            _real_change = True
                            break
                    except Exception:
                        continue
            if not _real_change:
                return
        except Exception:
            return
        try:
            if not is_blender_focused():
                return
        except Exception:
            pass
        try:
            scene = _resolve_scene_for_tick()
            if scene is None:
                return
            p = scene.track_timer
        except Exception:
            return
        fe["running"] = True
        global _last_tick_mono
        _last_tick_mono = time.monotonic()
        try:
            p.session_start_str = _now_str()
            if not p.project_start_str:
                p.project_start_str = _now_str()
        except Exception:
            pass
        try:
            _sync_all_scenes()
        except Exception:
            pass
    except Exception:
        pass


@bpy.app.handlers.persistent
def _on_render_pre(dummy):
    global _render_active, _render_start_mono
    _render_active = True
    _render_start_mono = time.monotonic()


def _credit_render_job():
    """Credit a finished/cancelled foreground render (the UI was blocked)."""
    global _render_active, _render_start_mono
    if not _render_active:
        return
    _render_active = False
    try:
        elapsed = time.monotonic() - _render_start_mono
    except Exception:
        return
    if elapsed < 0:
        return
    if elapsed > 86400.0:
        elapsed = 86400.0
    try:
        fe = _file_entry()
        fe["total"] += elapsed
        fe["session"] += elapsed
        fe["render"] = fe.get("render", 0.0) + elapsed
        _sync_all_scenes()
    except Exception:
        pass


@bpy.app.handlers.persistent
def _on_render_post(dummy):
    _credit_render_job()


@bpy.app.handlers.persistent
def _on_render_cancel(dummy):
    _credit_render_job()


def _merge_sidecar_milestones(scene):
    """On open, keep the max between .blend and sidecar per step (uid, else name)."""
    try:
        data = _read_sidecar()
        if not data:
            return
        snap = data.get("milestones")
        if not isinstance(snap, list):
            return
        by_uid, by_name = {}, {}
        for h in snap:
            try:
                sec = float(h.get("seconds", 0.0) or 0.0)
                if h.get("uid"):
                    by_uid[h["uid"]] = max(by_uid.get(h["uid"], 0.0), sec)
                nm = (h.get("name") or "").strip().upper()
                if nm:
                    by_name[nm] = max(by_name.get(nm, 0.0), sec)
            except Exception:
                continue
        try:
            props = scene.track_timer
        except Exception:
            return
        entry = _get_entry(scene)
        ms = entry.get("ms", {})
        for m in props.milestones:
            try:
                uid = getattr(m, "uid", "")
            except Exception:
                continue
            if not uid or uid not in ms:
                continue
            best = ms[uid]["s"]
            if uid in by_uid:
                best = max(best, by_uid[uid])
            nm = (m.name or "").strip().upper()
            if nm in by_name:
                best = max(best, by_name[nm])
            ms[uid]["s"] = best
    except Exception:
        pass


@bpy.app.handlers.persistent
def _on_load_post(dummy):
    global _last_tick_mono, _last_sidecar_save, _last_props_sync, _last_drawn_int, _unfocused_since, _render_active
    _last_tick_mono = time.monotonic()
    _last_sidecar_save = 0.0
    _last_props_sync = 0.0
    _last_drawn_int = None
    _unfocused_since = None
    _render_active = False
    _probe_backends()
    try:
        _migrate_loose_files()
    except Exception:
        pass
    # a session left open by a close/crash becomes history (never lost)
    try:
        _recover_open_session()
    except Exception:
        pass
    _prune_store_to_current_file()
    # fresh open: eligible again (opening itself never counts)
    try:
        _paused_files.discard(_file_key())
    except Exception:
        pass
    # file truth adopts saved values (max with sidecar); sessions restart
    try:
        key = _file_key()
        if key in _file_state:
            del _file_state[key]
        fe = _file_entry()
        fe["session"] = 0.0
        fe["running"] = False
    except Exception:
        pass
    # steps keep their place (max with sidecar); only counting pauses
    try:
        for s in bpy.data.scenes:
            if hasattr(s, "track_timer"):
                try:
                    mkey = _store_key_for_scene(s)
                    if mkey in _time_store:
                        del _time_store[mkey]
                    _get_entry(s)
                    _merge_sidecar_milestones(s)
                except Exception:
                    pass
                try:
                    s.track_timer.running = False
                    s.track_timer.session_seconds = 0.0
                    s.track_timer.session_start_str = ""
                    s.track_timer.paused_reason = ""
                except Exception:
                    pass
                try:
                    _pp = _addon_prefs()
                    if _pp is not None:
                        if not s.track_timer.client_name and getattr(_pp, "client_name", ""):
                            s.track_timer.client_name = _pp.client_name
                        if not s.track_timer.project_name and getattr(_pp, "project_name", ""):
                            s.track_timer.project_name = _pp.project_name
                except Exception:
                    pass
        _sync_all_scenes()
    except Exception:
        pass
    # safety net: revive the timer if it ever died
    try:
        if not bpy.app.timers.is_registered(track_timer_tick):
            try:
                bpy.app.timers.register(track_timer_tick, first_interval=1.0, persistent=True)
            except TypeError:
                bpy.app.timers.register(track_timer_tick, first_interval=1.0)
    except Exception:
        pass


classes = (
    TrackTimerMilestone,
    TrackTimerProps,
    TrackTimerPreferences,
    TRACKTIMER_OT_start,
    TRACKTIMER_OT_pause,
    TRACKTIMER_OT_finish,
    TRACKTIMER_OT_reset_total,
    TRACKTIMER_OT_add_minutes,
    TRACKTIMER_OT_export_csv,
    TRACKTIMER_OT_report_generate,
    TRACKTIMER_OT_report_open_folder,
    TRACKTIMER_OT_report_html,
    TRACKTIMER_OT_app_add,
    TRACKTIMER_OT_app_remove,
    TRACKTIMER_OT_app_add_current,
    TRACKTIMER_OT_milestone_add,
    TRACKTIMER_OT_milestone_remove,
    TRACKTIMER_OT_milestone_toggle_active,
    TRACKTIMER_OT_milestone_toggle_done,
    TRACKTIMER_OT_milestone_move,
    TRACKTIMER_OT_milestone_clear_finished,
    TRACKTIMER_OT_milestone_template,
    TRACKTIMER_OT_milestone_add_minutes,
    TRACKTIMER_UL_milestones,
    TRACKTIMER_PT_panel,
)


def register():
    global _ADDON_ENABLED, _ATEXIT_REGISTERED
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.track_timer = bpy.props.PointerProperty(type=TrackTimerProps)
    global _last_tick_mono, _last_sidecar_save, _last_props_sync, _last_drawn_int, _unfocused_since, _last_fg, _last_fg_sig, _render_active, _render_start_mono
    _last_tick_mono = time.monotonic()
    _last_sidecar_save = 0.0
    _last_props_sync = 0.0
    _last_drawn_int = None
    _unfocused_since = None
    _last_fg = None
    _last_fg_sig = None
    _render_active = False
    _render_start_mono = 0.0
    _ADDON_ENABLED = True
    _apply_language()
    _probe_backends()
    try:
        _overlay_sync()
    except Exception:
        pass
    try:
        if not bpy.app.timers.is_registered(track_timer_tick):
            try:
                bpy.app.timers.register(track_timer_tick, first_interval=1.0, persistent=True)
            except TypeError:
                bpy.app.timers.register(track_timer_tick, first_interval=1.0)
    except Exception:
        try:
            bpy.app.timers.register(track_timer_tick, first_interval=1.0)
        except Exception:
            pass
    if _on_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load_post)
    try:
        if hasattr(bpy.app.handlers, "save_post") and _on_save_post not in bpy.app.handlers.save_post:
            bpy.app.handlers.save_post.append(_on_save_post)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "save_pre") and _on_save_pre not in bpy.app.handlers.save_pre:
            bpy.app.handlers.save_pre.append(_on_save_pre)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "depsgraph_update_post") and _on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "render_pre") and _on_render_pre not in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.append(_on_render_pre)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "render_post") and _on_render_post not in bpy.app.handlers.render_post:
            bpy.app.handlers.render_post.append(_on_render_post)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "render_cancel") and _on_render_cancel not in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.append(_on_render_cancel)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "load_pre") and _on_load_pre not in bpy.app.handlers.load_pre:
            bpy.app.handlers.load_pre.append(_on_load_pre)
    except Exception:
        pass
    if not _ATEXIT_REGISTERED:
        try:
            atexit.register(_on_blender_exit)
            _ATEXIT_REGISTERED = True
        except Exception:
            pass
    try:
        bpy.types.STATUSBAR_HT_header.append(draw_statusbar)
    except Exception:
        pass


def unregister():
    global _ADDON_ENABLED
    _ADDON_ENABLED = False
    try:
        _overlay_remove()
    except Exception:
        pass
    try:
        bpy.types.STATUSBAR_HT_header.remove(draw_statusbar)
    except Exception:
        pass
    try:
        if _on_load_post in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(_on_load_post)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "save_post") and _on_save_post in bpy.app.handlers.save_post:
            bpy.app.handlers.save_post.remove(_on_save_post)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "load_pre") and _on_load_pre in bpy.app.handlers.load_pre:
            bpy.app.handlers.load_pre.remove(_on_load_pre)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "save_pre") and _on_save_pre in bpy.app.handlers.save_pre:
            bpy.app.handlers.save_pre.remove(_on_save_pre)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "depsgraph_update_post") and _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "render_pre") and _on_render_pre in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.remove(_on_render_pre)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "render_post") and _on_render_post in bpy.app.handlers.render_post:
            bpy.app.handlers.render_post.remove(_on_render_post)
    except Exception:
        pass
    try:
        if hasattr(bpy.app.handlers, "render_cancel") and _on_render_cancel in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(_on_render_cancel)
    except Exception:
        pass
    try:
        if bpy.app.timers.is_registered(track_timer_tick):
            bpy.app.timers.unregister(track_timer_tick)
    except Exception:
        pass
    try:
        del bpy.types.Scene.track_timer
    except Exception:
        pass
    for c in reversed(classes):
        try:
            bpy.utils.unregister_class(c)
        except Exception:
            pass


if __name__ == "__main__":
    register()
