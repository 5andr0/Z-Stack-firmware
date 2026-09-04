#!/usr/bin/env python3
"""Add deterministic commissioning diagnostics to the patched GenericApp source."""

from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, description: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one {description} anchor, found {count}"
        )
    return text.replace(old, new, 1)


def instrument(source_path: Path) -> None:
    source = source_path.read_text(encoding="utf-8")

    source = replace_once(
        source,
        '#include <ti/drivers/apps/Button.h>\n',
        '#include <ti/drivers/apps/Button.h>\n#include <ti/display/Display.h>\n',
        "Display include",
    )

    source = replace_once(
        source,
        '/*********************************************************************\n * CONSTANTS\n */\n',
        '/*********************************************************************\n * CONSTANTS\n */\n\n'
        '#define HUE_STEERING_RETRY_DELAY 10000\n',
        "constants section",
    )

    source = replace_once(
        source,
        'static Button_Handle gRightButtonHandle;\n'
        'static Button_Handle gLeftButtonHandle;\n',
        'static Button_Handle gRightButtonHandle;\n'
        'static Button_Handle gLeftButtonHandle;\n'
        'static Display_Handle hueLogDisplay;\n'
        'static ClockP_Handle hueSteeringRetryClkHandle;\n'
        'static ClockP_Struct hueSteeringRetryClkStruct;\n',
        "global handles",
    )

    source = replace_once(
        source,
        'static void zclGenericApp_initializeClocks(void);\n'
        'static void Initialize_UI(void);\n',
        'static void zclGenericApp_initializeClocks(void);\n'
        'static void zclGenericApp_processSteeringRetryTimeoutCallback(UArg a0);\n'
        'static void zclGenericApp_scheduleSteeringRetry(void);\n'
        'static const char *hueBdbModeName(uint8_t mode);\n'
        'static const char *hueBdbStatusName(uint8_t status);\n'
        'static const char *hueDeviceStateName(zstack_DevState state);\n'
        'static void Initialize_UI(void);\n',
        "local function declarations",
    )

    source = replace_once(
        source,
        '/*********************************************************************\n * STATUS STRINGS\n */\n\n// TODO?\n',
        '''/*********************************************************************
 * STATUS STRINGS
 */

static const char *hueBdbModeName(uint8_t mode)
{
  switch (mode)
  {
    case BDB_COMMISSIONING_INITIALIZATION: return "INITIALIZATION";
    case BDB_COMMISSIONING_NWK_STEERING: return "NWK_STEERING";
    case BDB_COMMISSIONING_FORMATION: return "FORMATION";
    case BDB_COMMISSIONING_FINDING_BINDING: return "FINDING_BINDING";
    case BDB_COMMISSIONING_TOUCHLINK: return "TOUCHLINK";
    case BDB_COMMISSIONING_PARENT_LOST: return "PARENT_LOST";
    default: return "UNKNOWN_MODE";
  }
}

static const char *hueBdbStatusName(uint8_t status)
{
  switch (status)
  {
    case BDB_COMMISSIONING_SUCCESS: return "SUCCESS";
    case BDB_COMMISSIONING_IN_PROGRESS: return "IN_PROGRESS";
    case BDB_COMMISSIONING_NO_NETWORK: return "NO_NETWORK";
    case BDB_COMMISSIONING_TCLK_EX_FAILURE: return "TCLK_EX_FAILURE";
    case BDB_COMMISSIONING_NETWORK_RESTORED: return "NETWORK_RESTORED";
    case BDB_COMMISSIONING_FAILURE: return "FAILURE";
    default: return "OTHER_STATUS";
  }
}

static const char *hueDeviceStateName(zstack_DevState state)
{
  switch (state)
  {
    case zstack_DevState_HOLD: return "HOLD";
    case zstack_DevState_INIT: return "INIT";
    case zstack_DevState_NWK_DISC: return "NWK_DISC";
    case zstack_DevState_NWK_JOINING: return "NWK_JOINING";
    case zstack_DevState_END_DEVICE_UNAUTH: return "UNAUTHENTICATED";
    case zstack_DevState_DEV_ROUTER: return "DEV_ROUTER";
    case zstack_DevState_NWK_ORPHAN: return "NWK_ORPHAN";
    default: return "OTHER_STATE";
  }
}
''',
        "status strings section",
    )

    source = replace_once(
        source,
        '''static void Initialize_UI(void)
{
    /* Initialize btns */
''',
        '''static void Initialize_UI(void)
{
    Display_init();
    hueLogDisplay = Display_open(Display_Type_UART, NULL);
    if (hueLogDisplay != NULL)
    {
        Display_printf(hueLogDisplay, 0, 0,
                       "[HUE] boot: serial=115200 8N1 firmware=20260904-debug1");
        Display_printf(hueLogDisplay, 0, 0,
                       "[HUE] endpoint=1 profile=0x0104 device=0x0100 router=1");
    }

    /* Initialize btns */
''',
        "UI initialization",
    )

    source = replace_once(
        source,
        '''  zstack_bdbStartCommissioningReq_t zstack_bdbStartCommissioningReq;
  zstack_bdbStartCommissioningReq.commissioning_mode = 0;
''',
        '''  zstack_bdbStartCommissioningReq_t zstack_bdbStartCommissioningReq;
  if (hueLogDisplay != NULL)
  {
    Display_printf(hueLogDisplay, 0, 0, "[HUE] BDB restore/initialize request");
  }
  zstack_bdbStartCommissioningReq.commissioning_mode = 0;
''',
        "initial commissioning request",
    )

    source = replace_once(
        source,
        '''static void zclGenericApp_initializeClocks(void)
{
#if ZG_BUILD_ENDDEVICE_TYPE
''',
        '''static void zclGenericApp_initializeClocks(void)
{
    hueSteeringRetryClkHandle = UtilTimer_construct(
        &hueSteeringRetryClkStruct,
        zclGenericApp_processSteeringRetryTimeoutCallback,
        HUE_STEERING_RETRY_DELAY,
        0, false, 0);

#if ZG_BUILD_ENDDEVICE_TYPE
''',
        "clock initialization",
    )

    source = replace_once(
        source,
        '''
}

#if ZG_BUILD_ENDDEVICE_TYPE
/*******************************************************************************
 * @fn      zclGenericApp_processEndDeviceRejoinTimeoutCallback
''',
        '''
}

static void zclGenericApp_processSteeringRetryTimeoutCallback(UArg a0)
{
    (void)a0;
    appServiceTaskEvents |= GENERICAPP_EVT_1;
    Semaphore_post(appSemHandle);
}

static void zclGenericApp_scheduleSteeringRetry(void)
{
    if (hueSteeringRetryClkHandle != NULL)
    {
        UtilTimer_setTimeout(hueSteeringRetryClkHandle,
                             HUE_STEERING_RETRY_DELAY);
        UtilTimer_start(&hueSteeringRetryClkStruct);
        if (hueLogDisplay != NULL)
        {
            Display_printf(hueLogDisplay, 0, 0,
                           "[HUE] retrying network steering in 10 seconds");
        }
    }
}

#if ZG_BUILD_ENDDEVICE_TYPE
/*******************************************************************************
 * @fn      zclGenericApp_processEndDeviceRejoinTimeoutCallback
''',
        "steering retry helpers",
    )

    source = replace_once(
        source,
        '''        if ( appServiceTaskEvents & GENERICAPP_EVT_1 )
        {

          appServiceTaskEvents &= ~GENERICAPP_EVT_1;
        }
''',
        '''        if ( appServiceTaskEvents & GENERICAPP_EVT_1 )
        {
          zstack_bdbStartCommissioningReq_t req;
          req.commissioning_mode = BDB_COMMISSIONING_MODE_NWK_STEERING;
          if (hueLogDisplay != NULL)
          {
            Display_printf(hueLogDisplay, 0, 0,
                           "[HUE] retry: starting network steering");
          }
          Zstackapi_bdbStartCommissioningReq(appServiceTaskId, &req);
          appServiceTaskEvents &= ~GENERICAPP_EVT_1;
        }
''',
        "event-one handler",
    )

    source = replace_once(
        source,
        '''          zstack_bdbCBKETCLinkKeyExchangeAttemptReq.didSuccess = FALSE;

          Zstackapi_bdbCBKETCLinkKeyExchangeAttemptReq(appServiceTaskId,
''',
        '''          zstack_bdbCBKETCLinkKeyExchangeAttemptReq.didSuccess = FALSE;
          if (hueLogDisplay != NULL)
          {
            Display_printf(hueLogDisplay, 0, 0,
                           "[HUE] Trust Center exchange: use standard Zigbee 3 key procedure");
          }

          Zstackapi_bdbCBKETCLinkKeyExchangeAttemptReq(appServiceTaskId,
''',
        "Trust Center callback",
    )

    source = replace_once(
        source,
        '''        case zstackmsg_CmdIDs_BDB_FILTER_NWK_DESCRIPTOR_IND:

         /*   User logic to remove networks that do not want to join
          *   Networks to be removed can be released with Zstackapi_bdbNwkDescFreeReq
          */

          Zstackapi_bdbFilterNwkDescComplete(appServiceTaskId);
        break;
''',
        '''        case zstackmsg_CmdIDs_BDB_FILTER_NWK_DESCRIPTOR_IND:
        {
          zstackmsg_bdbFilterNwkDescriptorInd_t *pInd =
              (zstackmsg_bdbFilterNwkDescriptorInd_t *)pMsg;
          networkDesc_t *pNwk = pInd->bdbFilterNetworkDesc.pBDBListNwk;
          uint8_t index = 0;

          if (hueLogDisplay != NULL)
          {
            Display_printf(hueLogDisplay, 0, 0,
                           "[HUE] scan complete: candidate networks=%u",
                           pInd->bdbFilterNetworkDesc.count);
          }
          while ((pNwk != NULL) && (index < pInd->bdbFilterNetworkDesc.count))
          {
            if (hueLogDisplay != NULL)
            {
              Display_printf(hueLogDisplay, 0, 0,
                             "[HUE] network[%u]: pan=0x%04X channel=%u join-capacity=%u lqi=%u",
                             index, pNwk->panId, pNwk->logicalChannel,
                             pNwk->routerCapacity, pNwk->chosenRouterLinkQuality);
            }
            pNwk = (networkDesc_t *)pNwk->nextDesc;
            index++;
          }
          Zstackapi_bdbFilterNwkDescComplete(appServiceTaskId);
        }
        break;
''',
        "network descriptor callback",
    )

    source = replace_once(
        source,
        '''        case zstackmsg_CmdIDs_DEV_STATE_CHANGE_IND:
        {
            // The ZStack Thread is indicating a State change
//            zstackmsg_devStateChangeInd_t *pInd =
//                (zstackmsg_devStateChangeInd_t *)pMsg;
//                  UI_DeviceStateUpdated(&(pInd->req));
        }
        break;
''',
        '''        case zstackmsg_CmdIDs_DEV_STATE_CHANGE_IND:
        {
            zstackmsg_devStateChangeInd_t *pInd =
                (zstackmsg_devStateChangeInd_t *)pMsg;
            if (hueLogDisplay != NULL)
            {
              Display_printf(hueLogDisplay, 0, 0,
                             "[HUE] device state: %s (%u)",
                             hueDeviceStateName(pInd->req.state), pInd->req.state);
            }
            if (pInd->req.state == zstack_DevState_DEV_ROUTER)
            {
              zstack_sysNwkInfoReadRsp_t rsp = {0};
              Zstackapi_sysNwkInfoReadReq(appServiceTaskId, &rsp);
              if (hueLogDisplay != NULL)
              {
                Display_printf(hueLogDisplay, 0, 0,
                               "[HUE] JOINED: pan=0x%04X channel=%u short=0x%04X",
                               rsp.panId, rsp.logicalChannel, rsp.nwkAddr);
              }
            }
        }
        break;
''',
        "device-state callback",
    )

    source = replace_once(
        source,
        '''static void zclGenericApp_processAfIncomingMsgInd(zstack_afIncomingMsgInd_t *pInMsg)
{
    afIncomingMSGPacket_t afMsg;
''',
        '''static void zclGenericApp_processAfIncomingMsgInd(zstack_afIncomingMsgInd_t *pInMsg)
{
    afIncomingMSGPacket_t afMsg;
    uint16_t srcAddr = 0xFFFF;

    if ((pInMsg->srcAddr.addrMode == zstack_AFAddrMode_SHORT) ||
        (pInMsg->srcAddr.addrMode == zstack_AFAddrMode_GROUP) ||
        (pInMsg->srcAddr.addrMode == zstack_AFAddrMode_BROADCAST))
    {
        srcAddr = pInMsg->srcAddr.addr.shortAddr;
    }
    if (hueLogDisplay != NULL)
    {
        Display_printf(hueLogDisplay, 0, 0,
                       "[HUE] AF RX: src=0x%04X srcEp=%u dstEp=%u cluster=0x%04X len=%u rssi=%d lqi=%u",
                       srcAddr, pInMsg->srcAddr.endpoint, pInMsg->endpoint,
                       pInMsg->clusterId, pInMsg->n_payload, pInMsg->rssi,
                       pInMsg->linkQuality);
        if ((pInMsg->pPayload != NULL) && (pInMsg->n_payload >= 3))
        {
            Display_printf(hueLogDisplay, 0, 0,
                           "[HUE] AF bytes: %02X %02X %02X %02X %02X",
                           pInMsg->pPayload[0], pInMsg->pPayload[1],
                           pInMsg->pPayload[2],
                           pInMsg->n_payload > 3 ? pInMsg->pPayload[3] : 0,
                           pInMsg->n_payload > 4 ? pInMsg->pPayload[4] : 0);
        }
    }
''',
        "incoming AF diagnostics",
    )

    source = replace_once(
        source,
        '''static void zclGenericApp_ProcessCommissioningStatus(bdbCommissioningModeMsg_t *bdbCommissioningModeMsg)
{
  zstack_bdbStartCommissioningReq_t zstack_bdbStartCommissioningReq;
  switch(bdbCommissioningModeMsg->bdbCommissioningMode)
''',
        '''static void zclGenericApp_ProcessCommissioningStatus(bdbCommissioningModeMsg_t *bdbCommissioningModeMsg)
{
  zstack_bdbStartCommissioningReq_t zstack_bdbStartCommissioningReq;
  if (hueLogDisplay != NULL)
  {
    Display_printf(hueLogDisplay, 0, 0,
                   "[HUE] BDB: mode=%s(%u) status=%s(%u) remaining=0x%02X",
                   hueBdbModeName(bdbCommissioningModeMsg->bdbCommissioningMode),
                   bdbCommissioningModeMsg->bdbCommissioningMode,
                   hueBdbStatusName(bdbCommissioningModeMsg->bdbCommissioningStatus),
                   bdbCommissioningModeMsg->bdbCommissioningStatus,
                   bdbCommissioningModeMsg->bdbRemainingCommissioningModes);
  }
  switch(bdbCommissioningModeMsg->bdbCommissioningMode)
''',
        "commissioning status diagnostics",
    )

    source = replace_once(
        source,
        '''    case BDB_COMMISSIONING_NWK_STEERING:
      if(bdbCommissioningModeMsg->bdbCommissioningStatus == BDB_COMMISSIONING_SUCCESS)
      {
        //YOUR JOB:
        //We are on the nwk, what now?
      }
      else
      {
        //See the possible errors for nwk steering procedure
        //No suitable networks found
        //Want to try other channels?
        //try with bdb_setChannelAttribute
      }
    break;
''',
        '''    case BDB_COMMISSIONING_NWK_STEERING:
      if(bdbCommissioningModeMsg->bdbCommissioningStatus == BDB_COMMISSIONING_SUCCESS)
      {
        UtilTimer_stop(&hueSteeringRetryClkStruct);
      }
      else if(bdbCommissioningModeMsg->bdbCommissioningStatus != BDB_COMMISSIONING_IN_PROGRESS)
      {
        zclGenericApp_scheduleSteeringRetry();
      }
    break;
''',
        "network-steering result",
    )

    source = replace_once(
        source,
        '''    case BDB_COMMISSIONING_INITIALIZATION:
      zstack_bdbStartCommissioningReq.commissioning_mode = BDB_COMMISSIONING_MODE_NWK_STEERING | BDB_COMMISSIONING_MODE_FINDING_BINDING;
''',
        '''    case BDB_COMMISSIONING_INITIALIZATION:
      if (hueLogDisplay != NULL)
      {
        Display_printf(hueLogDisplay, 0, 0,
                       "[HUE] starting all-channel network steering");
      }
      zstack_bdbStartCommissioningReq.commissioning_mode = BDB_COMMISSIONING_MODE_NWK_STEERING | BDB_COMMISSIONING_MODE_FINDING_BINDING;
''',
        "initialization commissioning mode",
    )

    source = replace_once(
        source,
        '''static void zclGenericApp_OnOffCB( uint8_t cmd )
{
  switch ( cmd )
''',
        '''static void zclGenericApp_OnOffCB( uint8_t cmd )
{
  if (hueLogDisplay != NULL)
  {
    Display_printf(hueLogDisplay, 0, 0,
                   "[HUE] OnOff command=%u old-state=%u", cmd,
                   zclGenericApp_OnOff);
  }
  switch ( cmd )
''',
        "On/Off command diagnostics",
    )

    source = replace_once(
        source,
        '''    default:
      break;
  }
}

/*********************************************************************
 * @fn      zclGenericApp_SceneRecallCB
''',
        '''    default:
      break;
  }
  if (hueLogDisplay != NULL)
  {
    Display_printf(hueLogDisplay, 0, 0,
                   "[HUE] OnOff new-state=%u", zclGenericApp_OnOff);
  }
}

/*********************************************************************
 * @fn      zclGenericApp_SceneRecallCB
''',
        "On/Off result diagnostics",
    )

    source = replace_once(
        source,
        '''static uint8_t zclGenericApp_ProcessIncomingMsg( zclIncoming_t *pInMsg )
{
  uint8_t handled = FALSE;
''',
        '''static uint8_t zclGenericApp_ProcessIncomingMsg( zclIncoming_t *pInMsg )
{
  uint8_t handled = FALSE;

  if (hueLogDisplay != NULL)
  {
    Display_printf(hueLogDisplay, 0, 0,
                   "[HUE] ZCL external: cluster=0x%04X cmd=0x%02X seq=%u data=%u",
                   pInMsg->msg->clusterId, pInMsg->hdr.commandID,
                   pInMsg->hdr.transSeqNum, pInMsg->pDataLen);
  }
''',
        "external ZCL diagnostics",
    )

    source = replace_once(
        source,
        '''static void zclGenericApp_processKey(Button_Handle _btn)
{
    NLME_LeaveReq_t         req;
''',
        '''static void zclGenericApp_processKey(Button_Handle _btn)
{
    if (hueLogDisplay != NULL)
    {
        Display_printf(hueLogDisplay, 0, 0,
                       "[HUE] button: factory reset and reboot");
    }
    NLME_LeaveReq_t         req;
''',
        "factory-reset button diagnostics",
    )

    source_path.write_text(source, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    instrument(args.source)


if __name__ == "__main__":
    main()
