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
      OU.UNIT_NAME,
      IP.LEGAL_DSC,
      PR.LEGAL_NAME AS HOLDER_ORGANNSATION_NAME,
      PR.FIRST_NAME || ' ' || PR.LAST_NAME AS HOLDER_INDIVIDUAL_NAME,
      TE.PRIMARY_CONTACT_YRN,
      IH.CITY AS HOLDER_CITY,
      IH.REGION_CDE AS HOLDER_REGION,
      IH.COUNTRY_CDE AS HOLDER_COUNTRY,
      PR.WORK_AREA_CODE || PR.WORK_EXTENSION_NUMBER|| PR.WORK_PHONE_NUMBER AS HOLDER_PHONE
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
    ON OU.ORG_UNIT_SID = DT.ORG_UNIT_SID 
  JOIN WHSE_TANTALIS.TA_TENANTS TE 
    ON TE.DISPOSITION_TRANSACTION_SID = DT.DISPOSITION_TRANSACTION_SID
      AND TE.SEPARATION_DAT IS NULL
  JOIN (SELECT MIN (B.ROW_UNIQUEID), 
               B.DISPOSITION_TRANSACTION_SID,
               B.INTERESTED_PARTY_SID,
               B.ORGANIZATIONS_LEGAL_NAME,
               B.INDIVIDUALS_FIRST_NAME,
               B.INDIVIDUALS_LAST_NAME,
               B.CITY,
               B.COUNTRY_CDE,
               B.REGION_CDE
        FROM WHSE_TANTALIS.TA_INTEREST_HOLDER_VW B
        GROUP BY
               B.DISPOSITION_TRANSACTION_SID,
               B.INTERESTED_PARTY_SID,
               B.ORGANIZATIONS_LEGAL_NAME,
               B.INDIVIDUALS_FIRST_NAME,
               B.INDIVIDUALS_LAST_NAME,
               B.CITY,
               B.COUNTRY_CDE,
               B.REGION_CDE) IH
    ON IH.INTERESTED_PARTY_SID = TE.INTERESTED_PARTY_SID
      AND IH.DISPOSITION_TRANSACTION_SID = TE.DISPOSITION_TRANSACTION_SID
  JOIN WHSE_TANTALIS.TA_INTERESTED_PARTIES PR
    ON PR.INTERESTED_PARTY_SID = TE.INTERESTED_PARTY_SID
  JOIN WHSE_TANTALIS.TA_INTEREST_PARCEL_SHAPES SP
    ON SP.INTRID_SID = IP.INTRID_SID

ORDER BY TS.EFFECTIVE_DAT DESC;
