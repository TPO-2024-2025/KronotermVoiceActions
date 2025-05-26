import asyncio
import logging
import pymodbus.client
from .const import MODBUS_SLAVE_ID
from .kronoterm_models import RegisterAddress


log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s [%(levelname)-8s] %(module)s:%(funcName)s:%(lineno)d - %(message)s"
)

def deg_imenovalnik(deg: float) -> str:
    if deg == 1:
        return "ena stopinja"
    if deg == 2:
        return "dve stopinji"
    if deg == 3:
        return "tri stopinje"
    if deg == 4:
        return "štiri stopinje"
    if int(deg) == deg:
        return f"{int(deg)} stopinj"
    else:
        return f"{deg:.1f} stopinj"


def deg_tozilnik(deg: float) -> str:
    if deg == 1:
        return "eno stopinjo"
    if deg == 2:
        return "dve stopinji"
    if deg == 3:
        return "tri stopinje"
    if deg == 4:
        return "štiri stopinje"
    if int(deg) == deg:
        return f"{int(deg)} stopinj"
    else:
        return f"{deg:.1f} stopinj"


class MqttClient:

    def __init__(self, usb_port: int = 0):
        """Kronoterm heat pump mqtt client."""
        port = "/dev/ttyUSB" + str(usb_port)
        self.modbus_client = pymodbus.client.ModbusSerialClient(port, baudrate=115200)

    async def invoke_kronoterm_action(self, action: str, parameter: float | None):
        """Invokes an action on the Kronoterm heat pump."""
        handler = self.map_template_to_function.get(action)
        if handler is None:
            raise ValueError(f"Action '{action}' not supported")

        if parameter is None:
            # noinspection PyArgumentList
            return await handler(self)

        # noinspection PyArgumentList
        return await handler(self, parameter)


    async def read(self, addr: RegisterAddress, desc: str = "") -> int:
        """Read one Modbus holding register"""
        self.modbus_client.connect()
        rr = await asyncio.to_thread(
            self.modbus_client.read_holding_registers,
            addr.to_int() - 1,
            count=1,
            slave=MODBUS_SLAVE_ID
        )
        raw = rr.registers[0]
        value = raw - (raw >> 15 << 16)
        log.debug(f"{desc}: {value}")
        self.modbus_client.close()
        return value


    async def write(self, addr: RegisterAddress, raw: int):
        """Write a raw 16-bit word to a Modbus holding register."""
        self.modbus_client.connect()
        await asyncio.to_thread(
            self.modbus_client.write_register,
            addr.to_int() - 1,
            value=raw,
            slave=MODBUS_SLAVE_ID
        )
        log.debug(f"Written {raw} to address {addr}")
        self.modbus_client.close()


    async def read_temperature(self, addr: RegisterAddress, desc: str = "") -> float:
        """Read a temperature from a Modbus holding register, log a formatted value, return float"""
        signed = await self.read(addr, desc)
        val = signed / 10.0
        self.modbus_client.close()
        return val


    async def set_temperature(self, addr: RegisterAddress, temperature: float, desc: str = "") -> float:
        """Attempts to set the specified temperature and returns the actual new value"""
        raw = int(temperature * 10)
        await self.write(addr, raw)
        return await self.read_temperature(addr, desc)


    async def get_system_status(self) -> str:
        """Status delovanja celotne regulacije"""
        status = await self.read(RegisterAddress.SYSTEM_STATUS)
        if status == 1:
            return "Sistem je vklopljen."

        return "Sistem je izklopljen."


    async def get_operating_mode(self) -> str:
        """Funkcija delovanja, ki se izvaja"""
        mode_tag = await self.read(RegisterAddress.OPERATING_MODE)
        mode = "Neznano"
        match mode_tag:
            case 0: mode = "Ogrevanje"
            case 1: mode = "Sanitarna voda"
            case 2: mode = "Hlajenje"
            case 3: mode = "Ogrevanje bazena"
            case 4: mode = "Pregrevanje sanitarne vode"
            case 5: mode = "Mirovanje"
            case 7: mode = "Daljinski izklop"

        return f"Funkcija, ki se izvaja: {mode}."


    async def get_reserve_source_status(self) -> str:
        """Status rezervnega vira"""
        status = await self.read(RegisterAddress.RESERVE_SOURCE)
        if status == 1:
            return "Rezervni vir je vklopljen."

        return "Rezervni vir je izklopljen."


    async def get_alternative_source_status(self) -> str:
        """Status alternativnega vira"""
        status = await self.read(RegisterAddress.ALTERNATIVE_SOURCE)
        if status == 1:
            return "Alternativni vir je vklopljen."

        return "Alternativni vir je izklopljen."


    async def get_operation_regime_status(self) -> str:
        """Status režima delovanja"""
        status = await self.read(RegisterAddress.OPERATING_REGIME)
        regime = "Neznan"
        match status:
            case 0: regime = "Hlajenje"
            case 1: regime = "Ogrevanje"
            case 2: regime = "Ogrevanje in hlajenje izklopljeno"

        return f"Trenutno aktiven režim: {regime}."


    async def get_program_mode(self) -> str:
        """Dodatni programi delovanja"""
        mode = await self.read(RegisterAddress.PROGRAM_MODE)
        program = "Neznan"
        match mode:
            case 0: program = "Normalno delovanje"
            case 1: program = "Generalno delovanje v ECO režimu"
            case 2: program = "Generalno delovanje v COM režimu"
            case 3: program = "Program sušenja estrihov"

        return f"Trenutno aktiven dodaten program delovanja: {program}."


    async def get_dhw_quick_heat_status(self) -> str:
        """Status hitrega segrevanja sanitarne vode"""
        status = await self.read(RegisterAddress.DHW_QUICK_HEAT)
        if status == 1:
            return "Hitro segrevanje sanitarne vode je vklopljeno."

        return "Hitro segrevanje sanitarne vode je izklopljeno."


    async def get_defrost_mode_status(self) -> str:
        """Status odtaljevanja"""
        status = await self.read(RegisterAddress.DEFROST_MODE)
        if status == 1:
            return "Trenutno se izvaja odtaljevanje."

        return "Trenutno se odtaljevanje ne izvaja."


    async def turn_system_on(self) -> str:
        """Vklop sistema (toplotna črpalka in ogrevalni krogi)"""
        await self.write(RegisterAddress.SYSTEM_ON, 1)
        return "Vklop sistema uspešen."


    async def turn_system_off(self) -> str:
        """Izklop sistema (toplotna črpalka in ogrevalni krogi)"""
        await self.write(RegisterAddress.SYSTEM_ON, 0)
        return "Izklop sistema uspešen."


    async def set_regime_normal(self) -> str:
        """Nastavitev generalnega režima na normalni način"""
        await self.write(RegisterAddress.PROGRAM_SELECT, 0)
        return "Generalni režim nastavljen na normalni način."


    async def set_regime_eco(self) -> str:
        """Nastavitev generalnega režima na ECO način"""
        await self.write(RegisterAddress.PROGRAM_SELECT, 1)
        return "Generalni režim nastavljen na ECO način."


    async def set_regime_com(self) -> str:
        """Nastavitev generalnega režima na COM način"""
        await self.write(RegisterAddress.PROGRAM_SELECT, 2)
        return "Generalni režim nastavljen na COM način."


    async def enable_dhw_quick_heating(self) -> str:
        """Vklop hitrega segrevanja sanitarne vode"""
        await self.write(RegisterAddress.DHW_QUICK_HEAT_ENABLE, 1)
        return "Vklopljeno hitro segrevanje sanitarne vode."


    async def disable_dhw_quick_heating(self) -> str:
        """Izklop hitrega segrevanja sanitarne vode"""
        await self.write(RegisterAddress.DHW_QUICK_HEAT_ENABLE, 0)
        return "Izklopljeno hitro segrevanje sanitarne vode."


    async def get_heatpump_load(self) -> str:
        """Trenutna obremenitev toplotne črpalke v procentih"""
        load = await self.read(RegisterAddress.CURRENT_HP_LOAD)
        return f"Trenutna obremenjenost toplotne črpalke: {load} procentov."


    async def set_dhw_target_temperature(self, temperature: float) -> str:
        """Želena temperatura sanitarne vode"""
        actual = await self.set_temperature(RegisterAddress.DHW_TARGET_TEMP, temperature)
        warning = ""
        if actual < temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je previsoka. Najvišja "
                       f"podprta temperatura za sanitarno vodo je {deg_imenovalnik(actual)}.")
        elif actual > temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je prenizka. Najnižja "
                       f"podprta temperatura za sanitarno vodo je {deg_imenovalnik(actual)}.")

        return f"{warning} Želena temperatura sanitarne vode nastavljena na {deg_tozilnik(actual)}."


    async def get_dhw_target_temperature(self) -> str:
        """Trenutna želena temperatura sanitarne vode"""
        temp = await self.read_temperature(RegisterAddress.DHW_CURRENT_TARGET_TEMP)
        if temp == 500:
            return "Sanitarna voda je izklopljena."

        return f"Trenutna želena temperatura sanitarne vode je {deg_imenovalnik(temp)}."


    async def set_dhw_mode_disabled(self) -> str:
        """Izklopi delovanje sanitarne vode"""
        await self.write(RegisterAddress.DHW_MODE_SELECT, 0)
        return "Delovanje sanitarne vode izklopljeno."


    async def set_dhw_mode_normal(self) -> str:
        """Nastavi delovanje sanitarne vode na normalni režim"""
        await self.write(RegisterAddress.DHW_MODE_SELECT, 1)
        return "Nastavljeno delovanje sanitarne vode na normalni režim."


    async def set_dhw_mode_schedule(self) -> str:
        """Nastavi delovanje sanitarne vode na delovanje po urniku"""
        await self.write(RegisterAddress.DHW_MODE_SELECT, 2)
        return "Nastavljeno delovanje sanitarne vode na delovanje po urniku."


    async def get_dhw_schedule_mode(self) -> str:
        """Status delovanja sanitarne vode po urniku"""
        mode_tag = await self.read(RegisterAddress.DHW_SCHEDULE_STATUS)
        mode = "Neznano"
        match mode_tag:
            case 0: mode = "Izklopljeno"
            case 1: mode = "Normalno"
            case 2: mode = "ECO"
            case 3: mode = "COM"

        return f"Trenuten način delovanja sanitarne vode po urniku: {mode}"


    async def get_dhw_temperature(self) -> str:
        """Temperatura sanitarne vode"""
        temp = await self.read_temperature(RegisterAddress.DHW_TEMP)
        return f"Trenutna temperatura sanitarne vode je {deg_imenovalnik(temp)}."


    async def set_loop1_room_target_temp(self, temperature: float) -> str:
        """Želena temperatura 1. kroga"""
        actual = await self.set_temperature(RegisterAddress.LOOP_1_TARGET_ROOM_TEMP, temperature)
        warning = ""
        if actual < temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je previsoka. Najvišja "
                       f"podprta temperatura za prostor prvega kroga je {deg_imenovalnik(actual)}.")
        elif actual > temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je prenizka. Najnižja "
                       f"podprta temperatura za prostor prvega kroga je {deg_imenovalnik(actual)}.")

        return f"{warning} Želena temperatura prostora prvega kroga nastavljena na {deg_tozilnik(actual)}."


    async def get_loop1_room_target_temp(self) -> str:
        """Trenutna želena temperatura 1. kroga"""
        temp = await self.read_temperature(RegisterAddress.LOOP_1_CURRENT_TARGET_ROOM_TEMP)
        if temp == 500:
            return "Prvi ogrevalni krog je izklopljen."

        return f"Trenutna želena temperatura prostora prvega ogrevalnega kroga je {deg_imenovalnik(temp)}."


    async def set_loop1_operating_mode_disabled(self) -> str:
        """Izklopi 1. krog"""
        await self.write(RegisterAddress.LOOP_1_MODE_SELECT, 0)
        return "Prvi ogrevalni krog izklopljen."


    async def set_loop1_operating_mode_normal(self) -> str:
        """Nastavi delovanje 1. kroga na normalni režim"""
        await self.write(RegisterAddress.LOOP_1_MODE_SELECT, 1)
        return "Delovanje prvega ogrevalnega kroga nastavljeno na normalni režim."


    async def set_loop1_operating_mode_schedule(self) -> str:
        """Nastavi delovanje 1. kroga na delovanje po urniku"""
        await self.write(RegisterAddress.LOOP_1_MODE_SELECT, 2)
        return "Delovanje prvega ogrevalnega kroga nastavljeno na delovanje po urniku."


    async def get_loop1_operating_mode(self) -> str:
        """Status delovanja 1. kroga po urniku"""
        mode_tag = await self.read(RegisterAddress.LOOP_1_SCHEDULE_STATUS)
        mode = "Neznano"
        match mode_tag:
            case 0: mode = "Izklopljeno"
            case 1: mode = "Normalno"
            case 2: mode = "ECO"
            case 3: mode = "COM"

        return f"Trenutni status delovanja prvega kroga po urniku: {mode}."


    async def get_loop1_temp(self) -> str:
        """Temperatura 1. kroga"""
        temp = await self.read_temperature(RegisterAddress.LOOP_1_TEMP_SENSOR, "Loop 1 temperature")
        return f"Trenutna temperatura prvega ogrevalnega kroga: {deg_imenovalnik(temp)}."


    async def set_loop2_room_target_temp(self, temperature: float) -> str:
        """Želena temperatura prostora 2. kroga"""
        actual = await self.set_temperature(RegisterAddress.LOOP_2_TARGET_ROOM_TEMP, temperature)
        warning = ""
        if actual < temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je previsoka. Najvišja "
                       f"podprta temperatura za prostor drugega kroga je {deg_imenovalnik(actual)}.")
        elif actual > temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je prenizka. Najnižja "
                       f"podprta temperatura za prostor drugega kroga je {deg_imenovalnik(actual)}.")

        return f"{warning} Želena temperatura prostora drugega kroga nastavljena na {deg_tozilnik(actual)}."


    async def get_loop2_room_target_temp(self) -> str:
        """Trenutna želena temperatura prostora 2. kroga"""
        temp = await self.read_temperature(RegisterAddress.LOOP_2_CURRENT_TARGET_ROOM_TEMP)
        if temp == 500:
            return "Drugi ogrevalni krog je izklopljen."

        return f"Trenutna želena temperatura prostora drugega ogrevalnega je {deg_imenovalnik(temp)}."


    async def set_loop2_operating_mode_disabled(self) -> str:
        """Izklopi 2. krog"""
        await self.write(RegisterAddress.LOOP_2_MODE_SELECT, 0)
        return "Drugi ogrevalni krog izklopljen."


    async def set_loop2_operating_mode_normal(self) -> str:
        """Nastavi delovanje 2. kroga na normalni režim"""
        await self.write(RegisterAddress.LOOP_2_MODE_SELECT, 1)
        return "Delovanje drugega ogrevalnega kroga nastavljeno na normalni režim."


    async def set_loop2_operating_mode_schedule(self) -> str:
        """Nastavi delovanje 2. kroga na delovanje po urniku"""
        await self.write(RegisterAddress.LOOP_2_MODE_SELECT, 2)
        return "Delovanje drugega ogrevalnega kroga nastavljeno na delovanje po urniku."


    async def get_loop2_operating_mode(self) -> str:
        """Status delovanja 2. kroga po urniku"""
        mode_tag = await self.read(RegisterAddress.LOOP_2_SCHEDULE_STATUS)
        mode = "Neznano"
        match mode_tag:
            case 0: mode = "Izklopljeno"
            case 1: mode = "Normalno"
            case 2: mode = "ECO"
            case 3: mode = "COM"

        return f"Trenutni status delovanja drugega kroga po urniku: {mode}."


    async def get_loop2_temp(self) -> str:
        """Temperatura 2. kroga"""
        temp = await self.read_temperature(RegisterAddress.LOOP_2_TEMP_SENSOR)
        return f"Trenutna temperatura drugega ogrevalnega kroga: {deg_imenovalnik(temp)}."


    async def set_loop3_room_target_temp(self, temperature: float) -> str:
        """Želena temperatura prostora 3. kroga"""
        actual = await self.set_temperature(RegisterAddress.LOOP_3_ROOM_TARGET_TEMP, temperature)
        warning = ""
        if actual < temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je previsoka. Najvišja "
                       f"podprta temperatura za prostor tretjega kroga je {deg_imenovalnik(actual)}.")
        elif actual > temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je prenizka. Najnižja "
                       f"podprta temperatura za prostor tretjega kroga je {deg_imenovalnik(actual)}.")

        return f"{warning} Želena temperatura prostora tretjega kroga nastavljena na {deg_tozilnik(actual)}."


    async def get_loop3_room_target_temp(self) -> str:
        """Trenutna želena temperatura prostora 3. kroga"""
        temp = await self.read_temperature(RegisterAddress.LOOP_3_TARGET_ROOM_TEMP)
        if temp == 500:
            return "Tretji ogrevalni krog je izklopljen."

        return f"Trenutna želena temperatura tretjega ogrevalnega kroga je {deg_imenovalnik(temp)}."


    async def set_loop3_operating_mode_disabled(self) -> str:
        """Izklopi 3. krog"""
        await self.write(RegisterAddress.LOOP_3_MODE_SELECT, 0)
        return "Tretji ogrevalni krog izklopljen."


    async def set_loop3_operating_mode_normal(self) -> str:
        """Nastavi delovanje 3. kroga na normalni režim"""
        await self.write(RegisterAddress.LOOP_3_MODE_SELECT, 1)
        return "Delovanje tretjega ogrevalnega kroga nastavljeno na normalni režim."


    async def set_loop3_operating_mode_schedule(self) -> str:
        """Nastavi delovanje 3. kroga na delovanje po urniku"""
        await self.write(RegisterAddress.LOOP_3_MODE_SELECT, 2)
        return "Delovanje tretjega ogrevalnega kroga nastavljeno na delovanje po urniku."


    async def get_loop3_operating_mode(self) -> str:
        """Status delovanja 3. kroga po urniku"""
        mode_tag = await self.read(RegisterAddress.LOOP_3_SCHEDULE_STATUS)
        mode = "Neznano"
        match mode_tag:
            case 0: mode = "Izklopljeno"
            case 1: mode = "Normalno"
            case 2: mode = "ECO"
            case 3: mode = "COM"

        return f"Trenutni status delovanja tretjega kroga po urniku: {mode}."


    async def get_loop3_temp(self) -> str:
        """Temperatura 3. kroga"""
        temp = await self.read_temperature(RegisterAddress.LOOP_3_TEMP_SENSOR)
        return f"Trenutna temperatura tretjega ogrevalnega kroga: {deg_imenovalnik(temp)}."


    async def set_loop4_room_target_temp(self, temperature: float) -> str:
        """Želena temperatura prostora 4. kroga"""
        actual = await self.set_temperature(RegisterAddress.LOOP_4_ROOM_TARGET_TEMP, temperature)
        warning = ""
        if actual < temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je previsoka. Najvišja "
                       f"podprta temperatura za prostor četrtega kroga je {deg_imenovalnik(actual)}.")
        elif actual > temperature:
            warning = (f"Izbrana temperatura {deg_imenovalnik(temperature)} je prenizka. Najnižja "
                       f"podprta temperatura za prostor četrtega kroga je {deg_imenovalnik(actual)}.")

        return f"{warning} Želena temperatura prostora četrtega kroga nastavljena na {deg_tozilnik(actual)}."


    async def get_loop4_room_target_temp(self) -> str:
        """Trenutna želena temperatura prostora 4. kroga"""
        temp = await self.read_temperature(RegisterAddress.LOOP_4_TARGET_ROOM_TEMP)
        if temp == 500:
            return "Četrti ogrevalni krog je izklopljen."

        return f"Trenutna želena temperatura četrtega ogrevalnega kroga je {deg_imenovalnik(temp)}."


    async def set_loop4_operating_mode_disabled(self) -> str:
        """Izklopi 4. krog"""
        await self.write(RegisterAddress.LOOP_4_MODE_SELECT, 0)
        return "Četrti ogrevalni krog izklopljen."


    async def set_loop4_operating_mode_normal(self) -> str:
        """Nastavi delovanje 4. kroga na normalni režim"""
        await self.write(RegisterAddress.LOOP_4_MODE_SELECT, 1)
        return "Delovanje četrtega ogrevalnega kroga nastavljeno na normalni režim."


    async def set_loop4_operating_mode_schedule(self) -> str:
        """Nastavi delovanje 4. kroga na delovanje po urniku"""
        await self.write(RegisterAddress.LOOP_4_MODE_SELECT, 2)
        return "Delovanje četrtega ogrevalnega kroga nastavljeno na delovanje po urniku."


    async def get_loop4_operating_mode(self) -> str:
        """Status delovanja 4. kroga po urniku"""
        mode_tag = await self.read(RegisterAddress.LOOP_4_SCHEDULE_STATUS)
        mode = "Neznano"
        match mode_tag:
            case 0: mode = "Izklopljeno"
            case 1: mode = "Normalno"
            case 2: mode = "ECO"
            case 3: mode = "COM"

        return f"Trenutni status delovanja četrtega kroga po urniku: {mode}."


    async def get_loop4_temp(self) -> str:
        """Temperatura 4. kroga"""
        temp = await self.read_temperature(RegisterAddress.LOOP_4_TEMP_SENSOR)
        return f"Trenutna temperatura četrtega ogrevalnega kroga: {deg_imenovalnik(temp)}."


    async def get_outside_temp(self) -> str:
        """Zunanja temperatura"""
        temp = await self.read_temperature(RegisterAddress.OUTSIDE_TEMP, "Outside temperature")
        return f"Trenutna zunanja temperatura je {deg_imenovalnik(temp)}"


    map_template_to_function = {
        "ali je sistem vklopljen": get_system_status,
        "ali je sistem izklopljen": get_system_status,
        "kakšno je stanje sistema": get_system_status,

        "kakšna funkcija se izvaja": get_operating_mode,
        "kakšna funkcija delovanja se izvaja": get_operating_mode,

        "ali je rezervni vir vklopljen": get_reserve_source_status,
        "ali je rezervni vir izklopljen": get_reserve_source_status,
        "kakšen je status rezervnega vira": get_reserve_source_status,

        "ali je alternativni vir vklopljen": get_alternative_source_status,
        "ali je alternativni vir izklopljen": get_alternative_source_status,
        "kakšen je status alternativnega vira": get_alternative_source_status,

        "kakšen je trenuten režim delovanja": get_operation_regime_status,
        "kakšen je režim delovanja": get_operation_regime_status,

        "kakšen je trenuten program": get_program_mode,
        "kakšen je program delovanja": get_program_mode,

        "kakšen je status hitrega segrevanja sanitarne vode": get_dhw_quick_heat_status,
        "ali je hitro segrevanje sanitarne vode vklopljeno": get_dhw_quick_heat_status,
        "ali je hitro segrevanje sanitarne vode izklopljeno": get_dhw_quick_heat_status,

        "kakšen je status odtaljevanja": get_defrost_mode_status,
        "ali je odtaljevanje vklopljeno": get_defrost_mode_status,
        "ali je odtaljevanje izklopljeno": get_defrost_mode_status,
        "ali se odtaljevanje izvaja": get_defrost_mode_status,

        "vklopi sistem": turn_system_on,
        "vklopi toplotno črpalko in ogrevalne kroge": turn_system_on,

        "izklopi sistem": turn_system_off,
        "izklopi toplotno črpalko in ogrevalne kroge": turn_system_off,

        "nastavi normalen režim": set_regime_normal,
        "nastavi režim na normalen način": set_regime_normal,
        "vklopi normalen režim": set_regime_normal,

        "nastavi eco režim": set_regime_eco,
        "nastavi režim na eco način": set_regime_eco,
        "vklopi eco režim": set_regime_eco,

        "nastavi com režim": set_regime_com,
        "nastavi režim na com način": set_regime_com,
        "vklopi com režim": set_regime_com,

        "vklopi hitro segrevanje sanitarne vode": enable_dhw_quick_heating,

        "izklopi hitro segrevanje sanitarne vode": disable_dhw_quick_heating,

        "kakšna je trenutna obremenitev toplotne črpalke": get_heatpump_load,

        "nastavi želeno temperaturo sanitarne vode na <temperature> stopinj": set_dhw_target_temperature,
        "nastavi temperaturo sanitarne vode na <temperature> stopinj": set_dhw_target_temperature,
        "segrej sanitarno vodo na <temperature> stopinj": set_dhw_target_temperature,

        "kakšna je trenutna želena temperatura sanitarne vode": get_dhw_target_temperature,

        "izklopi segrevanje sanitarne vode": set_dhw_mode_disabled,

        "nastavi normalen režim sanitarne vode": set_dhw_mode_normal,
        "nastavi režim sanitarne vode na normalno": set_dhw_mode_normal,
        "vklopi normalen režim segrevanja sanitarne vode": set_dhw_mode_normal,

        "nastavi režim sanitarne vode po urniku": set_dhw_mode_schedule,
        "vklopi režim segrevanja sanitarne vode po urniku": set_dhw_mode_schedule,

        "kakšen je trenuten način delovanja sanitarne vode po urniku": get_dhw_schedule_mode,

        "kakšna je temperatura sanitarne vode": get_dhw_temperature,

        ####################################################################################################################
        # LOOP 1
        ####################################################################################################################

        "nastavi temperaturo prostora ena na <temperature> stopinj": set_loop1_room_target_temp,
        "nastavi želeno temperaturo prostora prvega kroga na <temperature> stopinj": set_loop1_room_target_temp,

        "kakšna je trenutna želena temperatura prostora prvega kroga": get_loop1_room_target_temp,
        "kakšna je trenutna želena temperatura prostora ena": get_loop1_room_target_temp,

        "izklopi prvi ogrevalni krog": set_loop1_operating_mode_disabled,
        "izklopi ogrevalni krog ena": set_loop1_operating_mode_disabled,

        "nastavi delovanje prvega ogrevalnega kroga na normalni režim": set_loop1_operating_mode_normal,
        "nastavi delovanje ogrevalnega kroga ena na normalni režim": set_loop1_operating_mode_normal,
        "vklopi normalni režim na ogrevalnem krogu ena": set_loop1_operating_mode_normal,
        "vklopi normalni režim na prvem ogrevalnem krogu": set_loop1_operating_mode_normal,

        "nastavi delovanje prvega ogrevalnega kroga na delovanje po urniku": set_loop1_operating_mode_schedule,
        "nastavi delovanje ogrevalnega kroga ena na delovanje po urniku": set_loop1_operating_mode_schedule,
        "vklopi delovanje po urniku na ogrevalnem krogu ena": set_loop1_operating_mode_schedule,
        "vklopi delovanje po urniku na prvem ogrevalnem krogu": set_loop1_operating_mode_schedule,

        "kakšen je status delovanja prvega ogrevalnega kroga": get_loop1_operating_mode,
        "kakšen je status delovanja ogrevalnega kroga ena": get_loop1_operating_mode,

        "kakšna je temperatura ogrevalnega kroga ena": get_loop1_temp,
        "kakšna je temperatura prvega ogrevalnega kroga": get_loop1_temp,

        ####################################################################################################################
        # LOOP 2
        ####################################################################################################################

        "nastavi temperaturo prostora dva na <temperature> stopinj": set_loop2_room_target_temp,
        "nastavi želeno temperaturo prostora drugega kroga na <temperature> stopinj": set_loop2_room_target_temp,

        "kakšna je trenutna želena temperatura prostora drugega kroga": get_loop2_room_target_temp,
        "kakšna je trenutna želena temperatura prostora dva": get_loop2_room_target_temp,

        "izklopi drugi ogrevalni krog": set_loop2_operating_mode_disabled,
        "izklopi ogrevalni krog dva": set_loop2_operating_mode_disabled,

        "nastavi delovanje drugega ogrevalnega kroga na normalni režim": set_loop2_operating_mode_normal,
        "nastavi delovanje ogrevalnega kroga dva na normalni režim": set_loop2_operating_mode_normal,
        "vklopi normalni režim na ogrevalnem krogu dva": set_loop2_operating_mode_normal,
        "vklopi normalni režim na drugem ogrevalnem krogu": set_loop2_operating_mode_normal,

        "nastavi delovanje drugega ogrevalnega kroga na delovanje po urniku": set_loop2_operating_mode_schedule,
        "nastavi delovanje ogrevalnega kroga dva na delovanje po urniku": set_loop2_operating_mode_schedule,
        "vklopi delovanje po urniku na ogrevalnem krogu dva": set_loop2_operating_mode_schedule,
        "vklopi delovanje po urniku na drugem ogrevalnem krogu": set_loop2_operating_mode_schedule,

        "kakšen je status delovanja drugega ogrevalnega kroga": get_loop2_operating_mode,
        "kakšen je status delovanja ogrevalnega kroga dva": get_loop2_operating_mode,

        "kakšna je temperatura ogrevalnega kroga dva": get_loop2_temp,
        "kakšna je temperatura drugega ogrevalnega kroga": get_loop2_temp,

        ####################################################################################################################
        # LOOP 3
        ####################################################################################################################

        "nastavi temperaturo prostora tri na <temperature> stopinj": set_loop3_room_target_temp,
        "nastavi želeno temperaturo prostora tretjega kroga na <temperature> stopinj": set_loop3_room_target_temp,

        "kakšna je trenutna želena temperatura prostora tretjega kroga": get_loop3_room_target_temp,
        "kakšna je trenutna želena temperatura prostora tri": get_loop3_room_target_temp,

        "izklopi tretji ogrevalni krog": set_loop3_operating_mode_disabled,
        "izklopi ogrevalni krog tri": set_loop3_operating_mode_disabled,

        "nastavi delovanje tretjega ogrevalnega kroga na normalni režim": set_loop3_operating_mode_normal,
        "nastavi delovanje ogrevalnega kroga tri na normalni režim": set_loop3_operating_mode_normal,
        "vklopi normalni režim na ogrevalnem krogu tri": set_loop3_operating_mode_normal,
        "vklopi normalni režim na tretjem ogrevalnem krogu": set_loop3_operating_mode_normal,

        "nastavi delovanje tretjega ogrevalnega kroga na delovanje po urniku": set_loop3_operating_mode_schedule,
        "nastavi delovanje ogrevalnega kroga tri na delovanje po urniku": set_loop3_operating_mode_schedule,
        "vklopi delovanje po urniku na ogrevalnem krogu tri": set_loop3_operating_mode_schedule,
        "vklopi delovanje po urniku na tretjem ogrevalnem krogu": set_loop3_operating_mode_schedule,

        "kakšen je status delovanja tretjega ogrevalnega kroga": get_loop3_operating_mode,
        "kakšen je status delovanja ogrevalnega kroga tri": get_loop3_operating_mode,

        "kakšna je temperatura ogrevalnega kroga tri": get_loop3_temp,
        "kakšna je temperatura tretjega ogrevalnega kroga": get_loop3_temp,

        ####################################################################################################################
        # LOOP 4
        ####################################################################################################################

        "nastavi temperaturo prostora štiri na <temperature> stopinj": set_loop4_room_target_temp,
        "nastavi želeno temperaturo prostora četrtega kroga na <temperature> stopinj": set_loop4_room_target_temp,

        "kakšna je trenutna želena temperatura prostora četrtega kroga": get_loop4_room_target_temp,
        "kakšna je trenutna želena temperatura prostora štiri": get_loop4_room_target_temp,

        "izklopi četrti ogrevalni krog": set_loop4_operating_mode_disabled,
        "izklopi ogrevalni krog štiri": set_loop4_operating_mode_disabled,

        "nastavi delovanje četrtega ogrevalnega kroga na normalni režim": set_loop4_operating_mode_normal,
        "nastavi delovanje ogrevalnega kroga štiri na normalni režim": set_loop4_operating_mode_normal,
        "vklopi normalni režim na ogrevalnem krogu štiri": set_loop4_operating_mode_normal,
        "vklopi normalni režim na četrtem ogrevalnem krogu": set_loop4_operating_mode_normal,

        "nastavi delovanje četrtega ogrevalnega kroga na delovanje po urniku": set_loop4_operating_mode_schedule,
        "nastavi delovanje ogrevalnega kroga štiri na delovanje po urniku": set_loop4_operating_mode_schedule,
        "vklopi delovanje po urniku na ogrevalnem krogu štiri": set_loop4_operating_mode_schedule,
        "vklopi delovanje po urniku na četrtem ogrevalnem krogu": set_loop4_operating_mode_schedule,

        "kakšen je status delovanja četrtega ogrevalnega kroga": get_loop4_operating_mode,
        "kakšen je status delovanja ogrevalnega kroga štiri": get_loop4_operating_mode,

        "kakšna je temperatura ogrevalnega kroga štiri": get_loop4_temp,
        "kakšna je temperatura četrtega ogrevalnega kroga": get_loop4_temp,
    }
