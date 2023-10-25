SELECT* FROM(
SELECT
      CAST(IP.INTRID_SID AS NUMBER) INTRID_SID,
      CAST(DT.DISPOSITION_TRANSACTION_SID AS NUMBER) DISPOSITION_TRANSACTION_SID,
      DS.FILE_CHR AS FILE_NBR,
      SG.STAGE_NME AS STAGE,
      TT.ACTIVATION_CDE,
      TT.STATUS_NME AS STATUS,
      DT.APPLICATION_TYPE_CDE AS APPLICATION_TYPE,
      TS.EFFECTIVE_DAT AS EFFECTIVE_DATE,
      TY.TYPE_NME AS TENURE_TYPE,
      ST.SUBTYPE_NME AS TENURE_SUBTYPE,
      PU.PURPOSE_NME AS TENURE_PURPOSE,
      SP.SUBPURPOSE_NME AS TENURE_SUBPURPOSE,
      DT.DOCUMENT_CHR,
      DT.RECEIVED_DAT AS RECEIVED_DATE,
      DT.ENTERED_DAT AS ENTERED_DATE,
      DT.COMMENCEMENT_DAT AS COMMENCEMENT_DATE,
      DT.EXPIRY_DAT AS EXPIRY_DATE,
      IP.AREA_CALC_CDE,
      IP.AREA_HA_NUM AS AREA_HA,
      DT.LOCATION_DSC,
      OU.UNIT_NAME
      --SP.SHAPE
      
FROM WHSE_TANTALIS.TA_DISPOSITION_TRANSACTIONS DT 
  JOIN WHSE_TANTALIS.TA_INTEREST_PARCELS IP 
    ON DT.DISPOSITION_TRANSACTION_SID = IP.DISPOSITION_TRANSACTION_SID
      AND IP.EXPIRY_DAT IS NULL
  JOIN WHSE_TANTALIS.TA_DISP_TRANS_STATUSES TS
    ON DT.DISPOSITION_TRANSACTION_SID = TS.DISPOSITION_TRANSACTION_SID 
      AND TS.EXPIRY_DAT IS NULL
  JOIN WHSE_TANTALIS.TA_DISPOSITIONS DS
    ON DS.DISPOSITION_SID = DT.DISPOSITION_SID
  JOIN WHSE_TANTALIS.TA_STAGES SG 
    ON SG.CODE_CHR = TS.CODE_CHR_STAGE
  JOIN WHSE_TANTALIS.TA_STATUS TT 
    ON TT.CODE_CHR = TS.CODE_CHR_STATUS
  JOIN WHSE_TANTALIS.TA_AVAILABLE_TYPES TY 
    ON TY.TYPE_SID = DT.TYPE_SID    
  JOIN WHSE_TANTALIS.TA_AVAILABLE_SUBTYPES ST 
    ON ST.SUBTYPE_SID = DT.SUBTYPE_SID 
      AND ST.TYPE_SID = DT.TYPE_SID 
  JOIN WHSE_TANTALIS.TA_AVAILABLE_PURPOSES PU 
    ON PU.PURPOSE_SID = DT.PURPOSE_SID    
  JOIN WHSE_TANTALIS.TA_AVAILABLE_SUBPURPOSES SP 
    ON SP.SUBPURPOSE_SID = DT.SUBPURPOSE_SID 
      AND SP.PURPOSE_SID = DT.PURPOSE_SID 
   JOIN WHSE_TANTALIS.TA_ORGANIZATION_UNITS OU 
    ON OU.ORG_UNIT_SID = DT.ORG_UNIT_SID)TN 
    
WHERE TN.UNIT_NAME = 'VI - LAND MGMNT - VANCOUVER ISLAND SERVICE REGION'
  AND TN.STATUS = 'EXPIRED'
  
  AND TN.FILE_NBR NOT IN (SELECT CROWN_LANDS_FILE 
                          FROM WHSE_TANTALIS.TA_CROWN_TENURES_SVW
                          WHERE RESPONSIBLE_BUSINESS_UNIT = 'VI - LAND MGMNT - VANCOUVER ISLAND SERVICE REGION' 
                             AND TENURE_STATUS IN ('ACCEPTED', 'OFFERED', 'OFFER ACCEPTED', 'DISPOSITION IN GOOD STANDING'))  
 
                               
  AND TN.EXPIRY_DATE = (SELECT MAX(TG.EXPIRY_DATE)
                        FROM (SELECT
                                  CAST(IP.INTRID_SID AS NUMBER) INTRID_SID,
                                  CAST(DT.DISPOSITION_TRANSACTION_SID AS NUMBER) DISPOSITION_TRANSACTION_SID,
                                  DS.FILE_CHR AS FILE_NBR,
                                  DT.EXPIRY_DAT AS EXPIRY_DATE,
                                  TT.STATUS_NME AS STATUS
    
                              FROM WHSE_TANTALIS.TA_DISPOSITION_TRANSACTIONS DT 
                                JOIN WHSE_TANTALIS.TA_INTEREST_PARCELS IP 
                                  ON DT.DISPOSITION_TRANSACTION_SID = IP.DISPOSITION_TRANSACTION_SID
                                    AND IP.EXPIRY_DAT IS NULL
                                JOIN WHSE_TANTALIS.TA_DISP_TRANS_STATUSES TS
                                  ON DT.DISPOSITION_TRANSACTION_SID = TS.DISPOSITION_TRANSACTION_SID 
                                    AND TS.EXPIRY_DAT IS NULL
                                JOIN WHSE_TANTALIS.TA_DISPOSITIONS DS
                                  ON DS.DISPOSITION_SID = DT.DISPOSITION_SID
                                JOIN WHSE_TANTALIS.TA_STAGES SG 
                                  ON SG.CODE_CHR = TS.CODE_CHR_STAGE
                                JOIN WHSE_TANTALIS.TA_STATUS TT 
                                  ON TT.CODE_CHR = TS.CODE_CHR_STATUS
                                JOIN WHSE_TANTALIS.TA_AVAILABLE_TYPES TY 
                                  ON TY.TYPE_SID = DT.TYPE_SID    
                                JOIN WHSE_TANTALIS.TA_AVAILABLE_SUBTYPES ST 
                                  ON ST.SUBTYPE_SID = DT.SUBTYPE_SID 
                                    AND ST.TYPE_SID = DT.TYPE_SID 
                                JOIN WHSE_TANTALIS.TA_AVAILABLE_PURPOSES PU 
                                  ON PU.PURPOSE_SID = DT.PURPOSE_SID    
                                JOIN WHSE_TANTALIS.TA_AVAILABLE_SUBPURPOSES SP 
                                  ON SP.SUBPURPOSE_SID = DT.SUBPURPOSE_SID 
                                    AND SP.PURPOSE_SID = DT.PURPOSE_SID 
                                 JOIN WHSE_TANTALIS.TA_ORGANIZATION_UNITS OU 
                                  ON OU.ORG_UNIT_SID = DT.ORG_UNIT_SID)TG
                                  
                                WHERE TG.STATUS = 'EXPIRED'
                               AND  TG.FILE_NBR = TN.FILE_NBR
                                
                          GROUP BY TG.FILE_NBR)

ORDER BY TN.EFFECTIVE_DATE DESC;