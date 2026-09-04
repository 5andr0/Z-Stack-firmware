#!/usr/bin/env bash
set -euo pipefail

SDK="/opt/simplelink_cc13xx_cc26xx_sdk_8_30_01_01"
CCS="/opt/ccs/eclipse/eclipse"
COMPILER="/opt/ti-cgt-armllvm_4.0.2.LTS"
TARGET="zr_genericapp_CC1352P_2_LAUNCHXL_tirtos7_ticlang"
WORKSPACE="${HUE_ROUTER_WORKSPACE:-${SDK}/hue-router-workspace}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
BASE_PATCH="${REPO_ROOT}/router/Z-Stack_3.x.0/firmware.patch"
HUE_PATCH="${REPO_ROOT}/router/Z-Stack_3.x.0/hue_on_off_light.patch"
HUE_INSTRUMENTER="${REPO_ROOT}/.github/scripts/instrument-hue-router.py"
HUE_TCLK_CONFIGURER="${REPO_ROOT}/.github/scripts/configure-hue-tclk.py"
SYSCFG_OVERLAY="${REPO_ROOT}/router/Z-Stack_3.x.0/sonoff_zbdongle_p.syscfg.js"
HEX_VALIDATOR="${REPO_ROOT}/.github/scripts/validate_intel_hex.py"
DIST="${REPO_ROOT}/dist"
VARIANT="${HUE_ROUTER_VARIANT:-production}"

case "${VARIANT}" in
  production|debug) ;;
  *)
    echo "HUE_ROUTER_VARIANT must be 'production' or 'debug'" >&2
    exit 2
    ;;
esac

for required in "${SDK}" "${CCS}" "${COMPILER}/bin/tiarmobjcopy" \
                "${BASE_PATCH}" "${HUE_PATCH}" "${HUE_INSTRUMENTER}" \
                "${HUE_TCLK_CONFIGURER}" \
                "${SYSCFG_OVERLAY}" \
                "${HEX_VALIDATOR}"; do
  if [[ ! -e "${required}" ]]; then
    echo "Required build input is missing: ${required}" >&2
    exit 1
  fi
done

# Koenkk's patch is expressed against a materialized CCS project. CCS 12 keeps
# most project files as virtual links, so materialize only the target files in
# a staging tree, apply both patches there, and copy them back to their SDK
# source locations before creating the project.
STAGE_ROOT="$(mktemp -d)"
STAGE_PROJECT="${STAGE_ROOT}/${TARGET}"
mkdir -p \
  "${STAGE_PROJECT}/Application" \
  "${STAGE_PROJECT}/Common/zcl" \
  "${STAGE_PROJECT}/Stack/Config" \
  "${STAGE_PROJECT}/Stack/sys" \
  "${STAGE_PROJECT}/Stack/zdo"

cp "${SDK}/source/ti/zstack/apps/genericapp/zcl_genericapp.c" "${STAGE_PROJECT}/Application/"
cp "${SDK}/source/ti/zstack/apps/genericapp/zcl_genericapp.h" "${STAGE_PROJECT}/Application/"
cp "${SDK}/source/ti/zstack/apps/genericapp/zcl_genericapp_data.c" "${STAGE_PROJECT}/Application/"
cp "${SDK}/source/ti/zstack/stack/zcl/zcl.c" "${STAGE_PROJECT}/Common/zcl/"
cp "${SDK}/source/ti/zstack/config/f8wrouter.opts" "${STAGE_PROJECT}/Stack/Config/"
cp "${SDK}/source/ti/zstack/stack/sys/zcomdef.h" "${STAGE_PROJECT}/Stack/sys/"
cp "${SDK}/source/ti/zstack/stack/sys/zglobals.c" "${STAGE_PROJECT}/Stack/sys/"
cp "${SDK}/source/ti/zstack/stack/zdo/zd_app.c" "${STAGE_PROJECT}/Stack/zdo/"
cp "${SDK}/source/ti/zstack/boards/cc13x2_cc26x2/cc13x2_cc26x2_tirtos7_ticlang.cmd" "${STAGE_PROJECT}/"

BASE_INCLUDES=(
  "--include=${TARGET}/Application/zcl_genericapp.c"
  "--include=${TARGET}/Application/zcl_genericapp_data.c"
  "--include=${TARGET}/Common/zcl/zcl.c"
  "--include=${TARGET}/Stack/Config/f8wrouter.opts"
  "--include=${TARGET}/Stack/Config/preinclude.h"
  "--include=${TARGET}/Stack/sys/zcomdef.h"
  "--include=${TARGET}/Stack/sys/zglobals.c"
  "--include=${TARGET}/Stack/zdo/zd_app.c"
  "--include=${TARGET}/cc13x2_cc26x2_tirtos7_ticlang.cmd"
)

(
  cd "${STAGE_ROOT}"
  git apply --check --ignore-space-change "${BASE_INCLUDES[@]}" "${BASE_PATCH}"
  git apply --ignore-space-change "${BASE_INCLUDES[@]}" "${BASE_PATCH}"
  git apply --check --ignore-space-change "${HUE_PATCH}"
  git apply --ignore-space-change "${HUE_PATCH}"
)

if [[ "${VARIANT}" == "debug" ]]; then
  python3 "${HUE_INSTRUMENTER}" \
    "${STAGE_PROJECT}/Application/zcl_genericapp.c"
fi
python3 "${HUE_TCLK_CONFIGURER}" \
  "${STAGE_PROJECT}/Stack/Config/preinclude.h"

grep -q "ZCL_DEVICEID_ON_OFF_LIGHT" "${STAGE_PROJECT}/Application/zcl_genericapp_data.c"
grep -q "GENERICAPP_DEVICE_VERSION     1" "${STAGE_PROJECT}/Application/zcl_genericapp_data.c"
grep -q "zclGenericApp_OnOffCB" "${STAGE_PROJECT}/Application/zcl_genericapp.c"
grep -q "zstack_UseAPSKeyWithFallback" "${STAGE_PROJECT}/Application/zcl_genericapp.c"
grep -q "HUE_TCLK_KEY" "${STAGE_PROJECT}/Stack/Config/preinclude.h"
if [[ "${VARIANT}" == "debug" ]]; then
  grep -q "20260904-debug2" "${STAGE_PROJECT}/Application/zcl_genericapp.c"
  grep -q "commissioning key setup status" "${STAGE_PROJECT}/Application/zcl_genericapp.c"
else
  if grep -q "hueLogDisplay\|20260904-debug2" "${STAGE_PROJECT}/Application/zcl_genericapp.c"; then
    echo "Production source unexpectedly contains USB diagnostics" >&2
    exit 1
  fi
fi

install -m 0644 "${STAGE_PROJECT}/Application/zcl_genericapp.c" "${SDK}/source/ti/zstack/apps/genericapp/zcl_genericapp.c"
install -m 0644 "${STAGE_PROJECT}/Application/zcl_genericapp.h" "${SDK}/source/ti/zstack/apps/genericapp/zcl_genericapp.h"
install -m 0644 "${STAGE_PROJECT}/Application/zcl_genericapp_data.c" "${SDK}/source/ti/zstack/apps/genericapp/zcl_genericapp_data.c"
install -m 0644 "${STAGE_PROJECT}/Common/zcl/zcl.c" "${SDK}/source/ti/zstack/stack/zcl/zcl.c"
install -m 0644 "${STAGE_PROJECT}/Stack/Config/f8wrouter.opts" "${SDK}/source/ti/zstack/config/f8wrouter.opts"
install -m 0644 "${STAGE_PROJECT}/Stack/Config/preinclude.h" "${SDK}/source/ti/zstack/config/preinclude.h"
install -m 0644 "${STAGE_PROJECT}/Stack/sys/zcomdef.h" "${SDK}/source/ti/zstack/stack/sys/zcomdef.h"
install -m 0644 "${STAGE_PROJECT}/Stack/sys/zglobals.c" "${SDK}/source/ti/zstack/stack/sys/zglobals.c"
install -m 0644 "${STAGE_PROJECT}/Stack/zdo/zd_app.c" "${SDK}/source/ti/zstack/stack/zdo/zd_app.c"
install -m 0644 "${STAGE_PROJECT}/cc13x2_cc26x2_tirtos7_ticlang.cmd" "${SDK}/source/ti/zstack/boards/cc13x2_cc26x2/cc13x2_cc26x2_tirtos7_ticlang.cmd"

mkdir -p "${WORKSPACE}"

"${CCS}" -noSplash -data "${WORKSPACE}" \
  -application com.ti.ccstudio.apps.initialize \
  -ccs.toolDiscoveryPath /opt \
  -ccs.productDiscoveryPath /opt

PROJECT_SPEC="${SDK}/examples/rtos/CC1352P_2_LAUNCHXL/zstack/zr_genericapp/tirtos7/ticlang/${TARGET}.projectspec"
"${CCS}" -noSplash -data "${WORKSPACE}" \
  -application com.ti.ccstudio.apps.createProject \
  -ccs.projectSpec "${PROJECT_SPEC}" \
  -ccs.name "${TARGET}" \
  -ccs.endianness little \
  -ccs.toolChain TICLANG \
  -ccs.toolVersion TICLANG_4.0.2.LTS \
  -ccs.outputType executable \
  -ccs.setCompilerOptions "-include ${SDK}/source/ti/zstack/config/preinclude.h -DIS_ROUTER"

PROJECT_DIR="${WORKSPACE}/${TARGET}"
if [[ ! -f "${PROJECT_DIR}/zr_genericapp.syscfg" ]]; then
  echo "CCS did not create the expected project at ${PROJECT_DIR}" >&2
  exit 1
fi

printf '\n' >> "${PROJECT_DIR}/zr_genericapp.syscfg"
sed -e 's/\r$//' "${SYSCFG_OVERLAY}" >> "${PROJECT_DIR}/zr_genericapp.syscfg"

"${CCS}" -noSplash -data "${WORKSPACE}" \
  -application com.ti.ccstudio.apps.buildProject \
  -ccs.projects "${TARGET}" \
  -ccs.buildType full \
  -ccs.listErrors

OUT_FILE="$(find "${PROJECT_DIR}/default" -maxdepth 1 -type f -name '*.out' -print -quit)"
if [[ -z "${OUT_FILE}" ]]; then
  echo "Build finished without producing a .out file" >&2
  exit 1
fi

mkdir -p "${DIST}"
HEX_FILE="${DIST}/sonoff_zbdongle_p_hue_on_off_light_router_${VARIANT}.hex"
"${COMPILER}/bin/tiarmobjcopy" "${OUT_FILE}" --output-target ihex "${HEX_FILE}"

python3 "${HEX_VALIDATOR}" "${HEX_FILE}" \
  --min-data-bytes 0x10000 \
  --bootloader-config-address 0x57FD8 \
  --bootloader-config-bytes C50FFEC5
