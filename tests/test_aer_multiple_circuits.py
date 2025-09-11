# Copyright 2025 Scaleway
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from typing import Literal
import numpy as np
import random
import dotenv

from qiskit import QuantumCircuit
from qiskit_scaleway import ScalewayProvider

dotenv.load_dotenv()


def _random_qiskit_circuit(size: int) -> QuantumCircuit:
    num_qubits = size
    num_gate = size

    qc = QuantumCircuit(num_qubits)

    for _ in range(num_gate):
        random_gate = np.random.choice(["unitary", "cx", "cy", "cz"])

        if random_gate == "cx" or random_gate == "cy" or random_gate == "cz":
            control_qubit = np.random.randint(0, num_qubits)
            target_qubit = np.random.randint(0, num_qubits)

            while target_qubit == control_qubit:
                target_qubit = np.random.randint(0, num_qubits)

            getattr(qc, random_gate)(control_qubit, target_qubit)
        else:
            for q in range(num_qubits):
                random_gate = np.random.choice(["h", "x", "y", "z"])
                getattr(qc, random_gate)(q)

    qc.measure_all()

    return qc


def test_aer_multiple_circuits():

    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_SECRET_KEY"],
        url=os.getenv("QISKIT_SCALEWAY_API_URL"),
    )

    backend = provider.get_backend(os.getenv("QISKIT_SCALEWAY_BACKEND_NAME", "aer_simulation_pop_c16m128"))

    assert backend is not None

    session_id = backend.start_session(
        name="my-aer-session-autotest",
        deduplication_id=f"my-aer-session-autotest-{random.randint(1, 1000)}",
        max_duration="15m",
    )

    assert session_id is not None

    try:
        qc1 = _random_qiskit_circuit(20)
        qc2 = _random_qiskit_circuit(15)
        qc3 = _random_qiskit_circuit(21)
        qc4 = _random_qiskit_circuit(17)

        run_result = backend.run(
            [qc1, qc2, qc3, qc4],
            shots=1000,
            max_parallel_experiments=0,
            session_id=session_id,
        ).result()

        results = run_result.results

        assert len(results) == 4

        for result in results:
            assert result.success
    finally:
        backend.delete_session(session_id)


def _get_noise_model():
    import qiskit_aer.noise as noise

    # Error probabilities
    prob_1 = 0.001  # 1-qubit gate
    prob_2 = 0.01   # 2-qubit gate

    # Depolarizing quantum errors
    error_1 = noise.depolarizing_error(prob_1, 1)
    error_2 = noise.depolarizing_error(prob_2, 2)

    # Add errors to noise model
    noise_model = noise.NoiseModel()
    noise_model.add_all_qubit_quantum_error(error_1, ['rz', 'sx', 'x'])
    noise_model.add_all_qubit_quantum_error(error_2, ['cx'])

    return noise_model


def _bell_state_circuit():
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc


def _simple_one_state_circuit(init_state: Literal["0", "1"] = "0"):
    qc = QuantumCircuit(1, 1)
    if init_state == "1":
        qc.x(0)
    qc.measure_all()
    return qc


def test_aer_with_noise_model():

    provider = ScalewayProvider(
        project_id=os.environ["QISKIT_SCALEWAY_PROJECT_ID"],
        secret_key=os.environ["QISKIT_SCALEWAY_SECRET_KEY"],
        url=os.getenv("QISKIT_SCALEWAY_API_URL"),
    )

    backend = provider.get_backend(os.getenv("QISKIT_SCALEWAY_BACKEND_NAME", "aer_simulation_pop_c16m128"))

    assert backend is not None

    session_id = backend.start_session(
        name="my-aer-session-autotest",
        deduplication_id=f"my-aer-session-autotest-{random.randint(1, 1000)}",
        max_duration="15m",
    )

    assert session_id is not None

    try:
        qc1 = _bell_state_circuit()
        qc2 = _simple_one_state_circuit('0')
        qc3 = _simple_one_state_circuit('1')

        run_ideal_result = backend.run(
            [qc1, qc2, qc3],
            shots=1000,
            max_parallel_experiments=0,
            session_id=session_id,
        ).result()

        run_noisy_result = backend.run(
            [qc1, qc2, qc3],
            shots=1000,
            max_parallel_experiments=0,
            session_id=session_id,
            noise_model=_get_noise_model()
        ).result()

        ideal_results = run_ideal_result.results
        noisy_results = run_noisy_result.results

        assert len(ideal_results) == len(noisy_results) == 3

        for i, ideal_result in enumerate(ideal_results):
            assert len(ideal_result.data.counts) < len(noisy_results[i].data.counts)
    finally:
        backend.delete_session(session_id)


{'GJS_DEBUG_TOPICS': 'JS ERROR;JS LOG', 'LANGUAGE': 'en', 'USER': 'smagdela', 'LC_TIME': 'fr_FR.UTF-8', 'FONTCONFIG_PATH': '/etc/fonts', 'GIO_MODULE_DIR': '/home/smagdela/snap/code/common/.cache/gio-modules', 'XDG_SESSION_TYPE': 'wayland', 'GTK_EXE_PREFIX_VSCODE_SNAP_ORIG': '', 'GDK_BACKEND_VSCODE_SNAP_ORIG': '', 'SHLVL': '2', 'LESS': '-R', 'HOME': '/home/smagdela', 'LOCPATH_VSCODE_SNAP_ORIG': '', 'OLDPWD': '/home/smagdela/Documents/qiskit-scaleway', 'DESKTOP_SESSION': 'ubuntu', 'GTK_PATH': '/snap/code/205/usr/lib/x86_64-linux-gnu/gtk-3.0', 'NVM_BIN': '/home/smagdela/.nvm/versions/node/v24.7.0/bin', 'LSCOLORS': 'Gxfxcxdxbxegedabagacad', 'NVM_INC': '/home/smagdela/.nvm/versions/node/v24.7.0/include/node', 'ZSH': '/home/smagdela/.oh-my-zsh', 'XDG_DATA_HOME_VSCODE_SNAP_ORIG': '', 'GTK_IM_MODULE_FILE': '/home/smagdela/snap/code/common/.cache/immodules/immodules.cache', 'GNOME_SHELL_SESSION_MODE': 'ubuntu', 'GTK_MODULES': 'gail:atk-bridge', 'GSETTINGS_SCHEMA_DIR_VSCODE_SNAP_ORIG': '', 'PAGER': 'less', 'LC_MONETARY': 'fr_FR.UTF-8', 'MANAGERPID': '4094', 'SYSTEMD_EXEC_PID': '4472', 'GSM_SKIP_SSH_AGENT_WORKAROUND': 'true', 'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/1000/bus', 'GIT_TOKEN': 'P-FDofUbEdSBTpPkuUGxJG86MQp1OjJ6dgk.01.0z159r3sl', 'COLORTERM': 'truecolor', 'NVM_DIR': '/home/smagdela/.nvm', 'WAYLAND_DISPLAY': 'wayland-0', 'LOGNAME': 'smagdela', 'JOURNAL_STREAM': '9:33927', 'XDG_CONFIG_DIRS_VSCODE_SNAP_ORIG': '', 'MEMORY_PRESSURE_WATCH': '/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/session.slice/org.gnome.Shell@wayland.service/memory.pressure', 'XDG_SESSION_CLASS': 'user', 'XDG_DATA_DIRS_VSCODE_SNAP_ORIG': '/usr/local/share/:/usr/share/:/var/lib/snapd/desktop', 'USERNAME': 'smagdela', 'TERM': 'xterm-256color', 'GNOME_DESKTOP_SESSION_ID': 'this-is-deprecated', 'PATH': '/home/smagdela/Documents/qiskit-scaleway/.venv/bin:/home/smagdela/.nvm/versions/node/v24.7.0/bin:/home/smagdela/.local/bin:/home/smagdela/.local/share/gnome-shell/extensions/ddterm@amezin.github.com/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/snap/bin:/home/smagdela/.vscode/extensions/ms-python.debugpy-2025.10.0-linux-x64/bundled/scripts/noConfigScripts', 'SESSION_MANAGER': 'local/smagdela-ThinkPad-T14s-Gen-4:@/tmp/.ICE-unix/4411,unix/smagdela-ThinkPad-T14s-Gen-4:/tmp/.ICE-unix/4411', 'GTK_EXE_PREFIX': '/snap/code/205/usr', 'INVOCATION_ID': '74ca5276f26f49b8bff19734f8ce64fb', 'PAPERSIZE': 'a4', 'XDG_MENU_PREFIX': 'gnome-', 'LC_ADDRESS': 'fr_FR.UTF-8', 'GNOME_SETUP_DISPLAY': ':1', 'XDG_RUNTIME_DIR': '/run/user/1000', 'GIT_USER': 'smagdelaine', 'DISPLAY': ':0', 'LOCPATH': '/snap/code/205/usr/lib/locale', 'LANG': 'en_US.UTF-8', 'XDG_CURRENT_DESKTOP': 'Unity', 'LC_TELEPHONE': 'fr_FR.UTF-8', 'GIO_MODULE_DIR_VSCODE_SNAP_ORIG': '', 'XDG_DATA_HOME': '/home/smagdela/snap/code/205/.local/share', 'XMODIFIERS': '@im=ibus', 'XDG_SESSION_DESKTOP': 'ubuntu', 'XAUTHORITY': '/run/user/1000/.mutter-Xwaylandauth.P6OWC3', 'LS_COLORS': 'rs=0:di=01;34:ln=01;36:mh=00:pi=40;33:so=01;35:do=01;35:bd=40;33;01:cd=40;33;01:or=40;31;01:mi=00:su=37;41:sg=30;43:ca=00:tw=30;42:ow=34;42:st=37;44:ex=01;32:*.tar=01;31:*.tgz=01;31:*.arc=01;31:*.arj=01;31:*.taz=01;31:*.lha=01;31:*.lz4=01;31:*.lzh=01;31:*.lzma=01;31:*.tlz=01;31:*.txz=01;31:*.tzo=01;31:*.t7z=01;31:*.zip=01;31:*.z=01;31:*.dz=01;31:*.gz=01;31:*.lrz=01;31:*.lz=01;31:*.lzo=01;31:*.xz=01;31:*.zst=01;31:*.tzst=01;31:*.bz2=01;31:*.bz=01;31:*.tbz=01;31:*.tbz2=01;31:*.tz=01;31:*.deb=01;31:*.rpm=01;31:*.jar=01;31:*.war=01;31:*.ear=01;31:*.sar=01;31:*.rar=01;31:*.alz=01;31:*.ace=01;31:*.zoo=01;31:*.cpio=01;31:*.7z=01;31:*.rz=01;31:*.cab=01;31:*.wim=01;31:*.swm=01;31:*.dwm=01;31:*.esd=01;31:*.avif=01;35:*.jpg=01;35:*.jpeg=01;35:*.mjpg=01;35:*.mjpeg=01;35:*.gif=01;35:*.bmp=01;35:*.pbm=01;35:*.pgm=01;35:*.ppm=01;35:*.tga=01;35:*.xbm=01;35:*.xpm=01;35:*.tif=01;35:*.tiff=01;35:*.png=01;35:*.svg=01;35:*.svgz=01;35:*.mng=01;35:*.pcx=01;35:*.mov=01;35:*.mpg=01;35:*.mpeg=01;35:*.m2v=01;35:*.mkv=01;35:*.webm=01;35:*.webp=01;35:*.ogm=01;35:*.mp4=01;35:*.m4v=01;35:*.mp4v=01;35:*.vob=01;35:*.qt=01;35:*.nuv=01;35:*.wmv=01;35:*.asf=01;35:*.rm=01;35:*.rmvb=01;35:*.flc=01;35:*.avi=01;35:*.fli=01;35:*.flv=01;35:*.gl=01;35:*.dl=01;35:*.xcf=01;35:*.xwd=01;35:*.yuv=01;35:*.cgm=01;35:*.emf=01;35:*.ogv=01;35:*.ogx=01;35:*.aac=00;36:*.au=00;36:*.flac=00;36:*.m4a=00;36:*.mid=00;36:*.midi=00;36:*.mka=00;36:*.mp3=00;36:*.mpc=00;36:*.ogg=00;36:*.ra=00;36:*.wav=00;36:*.oga=00;36:*.opus=00;36:*.spx=00;36:*.xspf=00;36:*~=00;90:*#=00;90:*.bak=00;90:*.crdownload=00;90:*.dpkg-dist=00;90:*.dpkg-new=00;90:*.dpkg-old=00;90:*.dpkg-tmp=00;90:*.old=00;90:*.orig=00;90:*.part=00;90:*.rej=00;90:*.rpmnew=00;90:*.rpmorig=00;90:*.rpmsave=00;90:*.swp=00;90:*.tmp=00;90:*.ucf-dist=00;90:*.ucf-new=00;90:*.ucf-old=00;90:', 'SSH_AUTH_SOCK': '/run/user/1000/keyring/ssh', 'GSETTINGS_SCHEMA_DIR': '/home/smagdela/snap/code/205/.local/share/glib-2.0/schemas', 'SHELL': '/usr/bin/zsh', 'LC_NAME': 'fr_FR.UTF-8', 'QT_ACCESSIBILITY': '1', 'GDMSESSION': 'ubuntu', 'GTK_PATH_VSCODE_SNAP_ORIG': '', 'FONTCONFIG_FILE': '/etc/fonts/fonts.conf', 'GTK_IM_MODULE_FILE_VSCODE_SNAP_ORIG': '', 'LC_MEASUREMENT': 'fr_FR.UTF-8', 'GJS_DEBUG_OUTPUT': 'stderr', 'LC_IDENTIFICATION': 'fr_FR.UTF-8', 'QT_IM_MODULE': 'ibus', 'PWD': '/home/smagdela/Documents/qiskit-scaleway/tests', 'NVM_CD_FLAGS': '-q', 'XDG_DATA_DIRS': '/home/smagdela/snap/code/205/.local/share:/home/smagdela/snap/code/205:/snap/code/205/usr/share:/usr/local/share/:/usr/share/:/var/lib/snapd/desktop', 'LC_NUMERIC': 'fr_FR.UTF-8', 'LC_PAPER': 'fr_FR.UTF-8', 'MEMORY_PRESSURE_WRITE': 'c29tZSAyMDAwMDAgMjAwMDAwMAA=', 'VTE_VERSION': '7800', 'CHROME_DESKTOP': 'code.desktop', 'ORIGINAL_XDG_CURRENT_DESKTOP': 'ubuntu:GNOME', 'GDK_BACKEND': 'x11', 'TERM_PROGRAM': 'vscode', 'TERM_PROGRAM_VERSION': '1.103.2', 'PYDEVD_DISABLE_FILE_VALIDATION': '1', 'VSCODE_DEBUGPY_ADAPTER_ENDPOINTS': '/home/smagdela/.vscode/extensions/ms-python.debugpy-2025.10.0-linux-x64/.noConfigDebugAdapterEndpoints/endpoint-6061cecf75d47dd9.txt', 'BUNDLED_DEBUGPY_PATH': '/home/smagdela/.vscode/extensions/ms-python.debugpy-2025.10.0-linux-x64/bundled/libs/debugpy', 'GIT_ASKPASS': '/snap/code/205/usr/share/code/resources/app/extensions/git/dist/askpass.sh', 'VSCODE_GIT_ASKPASS_NODE': '/snap/code/205/usr/share/code/code', 'VSCODE_GIT_ASKPASS_EXTRA_ARGS': '', 'VSCODE_GIT_ASKPASS_MAIN': '/snap/code/205/usr/share/code/resources/app/extensions/git/dist/askpass-main.js', 'VSCODE_GIT_IPC_HANDLE': '/run/user/1000/vscode-git-2ba3223998.sock', 'VSCODE_INJECTION': '1', 'ZDOTDIR': '/home/smagdela', 'USER_ZDOTDIR': '/home/smagdela', 'VIRTUAL_ENV': '/home/smagdela/Documents/qiskit-scaleway/.venv', 'PS1': '(.venv) %(?:%{\x1b[01;32m%}%1{➜%} :%{\x1b[01;31m%}%1{➜%} ) %{\x1b[36m%}%c%{\x1b[00m%} $(git_prompt_info)', 'VIRTUAL_ENV_PROMPT': '(.venv) ', '_': '/home/smagdela/Documents/qiskit-scaleway/.venv/bin/pytest', 'PYTEST_VERSION': '8.4.2', 'QISKIT_IN_PARALLEL': 'FALSE', 'PYTEST_CURRENT_TEST': 'tests/test_aer_multiple_circuits.py::test_aer_multiple_circuits (call)', 'QISKIT_SCALEWAY_BACKEND_NAME': 'aer_simulation_local'}