import logging

logger = logging.getLogger(__name__)

import apdu as APDU


class Card:
    def __init__(self, connection, log_level=None):
        if log_level is not None:
            logging.basicConfig(level=log_level)

        self.__conn = connection
        self._check_connection()

    def _log_apdu(self, apdu_data):
        logger.debug("APDU:   " + APDU.get_hex(apdu_data))

    def _log_result(self, data, sw1, sw2):
        logger.debug("RESULT: (%s,%s) %s" % (hex(sw1), hex(sw2), APDU.get_hex(data)))

    def _send_apdu_raw(self, apdu_data):
        """
        Send APDU to card and return the data and status words.

        @param apdu_data: RAW APDU to send stored in a list
        @return: (data, sw1, sw2)
        """
        # Send the APDU
        self._log_apdu(apdu_data)
        data, sw1, sw2 = self.__conn.transmit(apdu_data)
        self._log_result(data, sw1, sw2)

        if sw1 != APDU.APDU_STATUS.SUCCESS:
            error_msg = "APDU ERROR: sw1=%x sw2=%x --- %s " % (
                sw1,
                sw2,
                APDU.get_status_msg(sw1, sw2),
            )

            logger.error(error_msg)
            raise Exception(error_msg)

        # Return our status and data
        return (data, sw1, sw2)

    def _check_connection(self):
        if self.__conn is None:
            error_msg = "No connection detected."
            logger.error(error_msg)
            raise Exception(error_msg)

    def _parse_attr(self, data, segment_start):
        """
        Parse the specified attribute from the base four profile data.

        @param data: profile data to parse
        @param segment_start: start of specified attribute segment

        @return: attribute data in string
        """

        # pos 0: always be 0xdf
        # pos 1: 0x2(2-5)
        # pos 2: attr length
        # pos 3 - n: attr data
        attr_lengh = data[segment_start + 2]
        attr_start = segment_start + 3
        attr_data = data[attr_start : attr_start + attr_lengh]
        return bytes(attr_data).decode("utf-8")

    def select_file_profile_ap(self):
        """
        SELECT FILE: 券面入力補助AP (DF)
        """
        apdu_select = APDU.SELECT_AP(data=APDU.APPLET.PROFILE)
        _, sw1, sw2 = self._send_apdu_raw(apdu_select)
        logger.info("券面入力補助AP: %x %x" % (sw1, sw2))

    def select_file_profile_pin(self):
        """
        SELECT FILE: 券面入力補助用PIN (EF)
        """
        apdu_select = APDU.SELECT_FILE(data=APDU.EF.PROFILE_PIN)
        _, sw1, sw2 = self._send_apdu_raw(apdu_select)
        logger.info("SELECT 券面入力補助用PIN: %x %x" % (sw1, sw2))

    def verify_profile_pin(self, pin_bytes):
        """
        VERIFY: 券面入力補助用PIN (パスワード)
        """
        apdu_verify = APDU.VERIFY_PIN(pin_bytes)
        _, sw1, sw2 = self._send_apdu_raw(apdu_verify)
        logger.info("VERIFY 券面入力補助用PIN: %x %x" % (sw1, sw2))

    def select_file_base_4_info(self):
        """
        SELECT FILE: 基本4情報 (EF)
        """
        apdu_select = APDU.SELECT_FILE(data=APDU.EF.BASE_FOUR)
        _, sw1, sw2 = self._send_apdu_raw(apdu_select)
        logger.info("基本4情報: %x %x" % (sw1, sw2))

    def read_binary_256(self):
        """
        READ BINARY: 256 bytes

        @return: 256 bytes of data
        """
        apdu_read = APDU.READ_BINARY(P1=0x00, P2=0x00)
        data, sw1, sw2 = self._send_apdu_raw(apdu_read)
        return data

    def get_basic_info(self, auth_pin):
        """
        基本4情報の取得

        @param auth_pin: 券面入力補助用PIN (パスワード)
        @return: (name, address, birthdate, gender): 名前、住所、生年月日、性別
        """

        # Connection Check
        self._check_connection()

        # SELECT FILE: 券面入力補助AP (DF)
        self.select_file_profile_ap()

        # SELECT FILE: 券面入力補助用PIN (EF)
        self.select_file_profile_pin()

        # VERIFY: 券面入力補助用PIN (パスワード)
        self.verify_profile_pin(pin_bytes=[ord(c) for c in auth_pin])

        # SELECT FILE: 基本4情報 (EF)
        self.select_file_base_4_info()

        # READ BINARY: 基本4情報の読み取り
        data = self.read_binary_256()

        name = self._parse_attr(data, data[APDU.BASE_FOUR_MANIFEST.NAME_SEGMENT_START])
        address = self._parse_attr(
            data, data[APDU.BASE_FOUR_MANIFEST.ADDRESS_SEGMENT_START]
        )
        birthdate = self._parse_attr(
            data, data[APDU.BASE_FOUR_MANIFEST.BIRTHDATE_SEGMENT_START]
        )
        gender = self._parse_attr(
            data, data[APDU.BASE_FOUR_MANIFEST.GENDER_SEGMENT_START]
        )

        return (name, address, birthdate, gender)
