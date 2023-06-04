''' motor_drivers.py
This file contains the classes for controlling the various motors in the lab. We have two types of motors: ThorLabs and Elliptec. There is a unique class for each type of motor.

authors:
Alec Roberson (aroberson@hmc.edu)
Ben Hartley (bhartley@hmc.edu)
'''

# imports 
from time import sleep
import serial
from typing import Union
import numpy as np
import thorlabs_apt as apt

# +++ variables +++

# com ports dictionary to keep track of connections
COM_PORTS = dict()

# active motors dictionary to keep track of motors that are going offline (when connections are closed)
LIVE_MOTORS = dict()

# +++ base class +++

class Motor:
    ''' Base class for all motor classes
    Handles naming, offset, and position tracking.
    
    Parameters
    ----------
    name : str
        The unique name for the motor.
    type : str
        The type of motor.
    offset : float
        The offset of the motor, in radians.
    '''
    def __init__(self, name:str, typ:str, offset:float=0):
        # set attributes
        self._name = name
        self._typ = typ
        self._offset = offset

        # keeping the position of the motor in local memory
        # this is the virtual position, after offset is applied
        self._pos = 0

        # add to motors dictionary
        LIVE_MOTORS[self._name] = self

    # +++ basic methods +++

    def __repr__(self) -> str:
        return f'{self.typ}Motor-{self.name}'
    
    def __str__(self) -> str:
        return self.__repr__()

    # +++ protected getters +++

    @property
    def name(self) -> str:
        ''' The name of this motor. '''
        return self._name
    
    @property
    def type(self) -> str:
        ''' The motor type. '''
        return self._typ

    @property
    def offset(self) -> float:
        ''' The zero position of this motor
        
        i.e. when we say the motor is at zero, where does it actually think it is
        '''
        return self._offset
    
    @property
    def pos(self) -> float:
        ''' The position of this motor '''
        return self._pos
    
    @property
    def is_active(self) -> bool:
        return self._is_active()
    
    @property
    def status(self) -> Union[str,int]:
        ''' Gets the status of the motor '''
        return self._get_status()

    # +++ private methods to be overridden +++

    def _get_position(self) -> float:
        ''' Gets the position of the motor in radians

        Returns
        -------
        float
            The position of the motor in radians.
        '''
        raise NotImplementedError
    
    def _set_position(self, angle_radians:float) -> float:
        ''' Sets the position of the motor in radians

        Parameters
        ----------
        angle_radians : float
            The position to set the motor to, in radians.
        
        Returns
        -------
        float
            The position of the motor in radians.
        '''
        raise NotImplementedError

    def _move_relative(self, angle_radians:float) -> float:
        ''' Moves the motor by an angle relative to it's current position

        Parameters
        ----------
        angle_radians : float
            The position to set the motor to, in radians.
        
        Returns
        -------
        float
            The position of the motor in radians.
        '''
        raise NotImplementedError

    def _is_active(self) -> bool:
        ''' Checks if the motor is active.

        Returns
        -------
        bool
            True if the motor is active, False otherwise.
        '''
        raise NotImplementedError

    def _get_status(self) -> Union[str,int]:
        ''' Gets the status of the motor

        Returns
        -------
        Union[str,int]
            The status of the motor. 0 indicates nominal status.
        '''
        raise NotImplementedError

    # +++ public methods +++

    def goto(self, angle_radians:float):
        ''' Sets the angle of the motor in radians

        Parameters
        ----------
        angle_radians : float
            The angle to set the motor to, in radians.
        '''
        # calculate the set point
        set_point = (angle_radians + self._offset) % (2*np.pi)

        # update the position, returning it as well
        self._pos = self._set_position(set_point) - self._offset
        return self._pos

    def move(self, angle_radians:float):
        ''' Moves the motor by an angle RELATIVE to it's current position

        Parameters
        ----------
        angle_radians : float
            The angle to move the motor by, in radians.
        '''
        # use the sub method
        self._pos = self._move_relative(angle_radians) - self._offset
        return self._pos

    def zero(self):
        ''' Returns this motor to it's zero position.
        
        Returns
        -------
        float
            The position of the motor in radians.
        '''
        return self.goto(0)
    
    def home(self):
        ''' Returns this motor to it's home position.
        
        Returns
        -------
        float
            The position of the motor in radians.
        '''
        # try to 
        abs_pos = self._set_position(0)
        # handle output
        if not isinstance(abs_pos, float):
            # get the position
            self._pos = self._get_position(0) - self._offset
            # raise error
            raise RuntimeError(f'Error homing {self.name}: {abs_pos}')
        else:
            self._pos = self._set_position(0) - self._offset
            return self._pos

# +++ subclasses of motor +++

class ElliptecMotor:
    ''' Elliptec Motor class.
    
    Parameters
    ----------
    name : str
        The unique name for the motor.
    com_port : str
        The COM port the motor is connected to.
    address : Union[str,bytes]
        The address of the motor, a single charachter.
    offset : float
        The offset of the motor, in radians. In other words, when the motor returns a position of zero, where does the actual motor hardware think it is?
    '''
    def __init__(self, name:str, com_port:str, address:Union[str,bytes], offset:float=0):
        # call super constructor
        super().__init__(name, 'Elliptec', offset)

        # self.com_port to serial port
        self.com_port = self._get_com_port(com_port)
        # self._addr to bytes
        self._addr = address is isinstance(address, bytes) and address or address.encode('utf-8')
        # a ton of stuff like model number and such as well as ppmu and travel
        self._get_info()

    # +++ status codes +++

    STATUS_CODES = {
        b'00': 0,
        b'01': 'communication time out',
        b'02': 'mechanical time out',
        b'03': 'invalid command',
        b'04': 'value out of range',
        b'05': 'module isolated',
        b'06': 'module out of isolation',
        b'07': 'initializing error',
        b'08': 'thermal error',
        b'09': 'busy',
        b'0A': 'sensor error',
        b'0B': 'motor error',
        b'0C': 'out of range error',
        b'0D': 'over current error'}

    # +++ protected getters +++
    
    @property
    def info(self) -> dict:
        ''' The hardware information about this motor. '''
        return self._info

    # +++ helper functions +++

    def _get_com_port(self, com_port:str) -> serial.Serial:
        ''' Retrieves the COM port Serial object. Opens a connection if necessary. '''
        # check if COM port is already open
        if com_port in COM_PORTS:
            return COM_PORTS[com_port]
        # otherwise open COM port
        else:
            try:
                s = serial.Serial(com_port, timeout=2)
                COM_PORTS[com_port] = s
                return s
            except:
                raise RuntimeError(f'Failed to connect to serial port {com_port} for motor {self.__repr__()}.')

    def _send_instruction(self, inst:bytes, data:bytes=b'', resp_len:int=None, require_resp_code:bytes=None) -> Union[bytes,None]:
        ''' Sends an instruction to the motor and gets a response if applicable.
        
        Parameters
        ----------
        inst : bytes
            The instruction to send, should be 2 bytes long.
        data : bytes, optional
            The data to send, if applicable.
        resp_len : int, optional
            The length of the response to require. If None, no response is expected.
        require_resp_code : bytes, optional
            The response code to require. If None, no response code check is performed.

        Returns
        -------
        bytes or None
            The response from the motor. None if no response is expected.
        '''
        # clear the queue if we want a response
        if resp_len is not None:
            self.com_port.readall()

        # send instruction
        self.com_port.write(self._addr + inst + data)

        if resp_len is not None:
            # read the response
            resp = self.com_port.read(resp_len)
            # check response code if applicable
            if require_resp_code is not None:
                if resp[1:3] != require_resp_code.upper():
                    raise RuntimeError(f'Expected response code {require_resp_code.upper()} but got {resp[2:3]}')
            # return the response
            return resp
    
    def _get_info(self) -> int:
        ''' Requests basic info from the motor. '''
        # return (143360/360)
        # get the info
        resp = self._send_instruction(b'in', resp_len=33, require_resp_code=b'in')
        # parse the info
        self._info = dict(
            ELL = str(resp[3:6]),
            SN = int(resp[5:13]),
            YEAR = int(resp[13:17]),
            FWREL = int(resp[17:19]),
            HWREL = int(resp[19:21])
        )
        # get travel and ppmu
        self._travel = int(resp[21:25], 16) # should be 360º
        self._ppmu = int(resp[25:33], 16)/self._travel
        return None

    def _radians_to_bytes(self, angle_radians:float, num_bytes:int=8) -> bytes:
        ''' Converts an angle in radians to a hexidecimal byte string.

        Parameters
        ----------
        angle_radians : float
            The angle to convert, in radians.
        num_bytes : int, optional
            The number of bytes to return. Default is 8.
        
        Returns
        -------
        '''
        # convert to degrees
        deg = np.rad2deg(angle_radians)
        # convert to pulses
        pulses = int(abs(deg) * self._ppmu)
        # if negative, take two's compliment
        if deg < 0:
            pulses = (pulses ^ 0xffffffff) + 1
        # convert to hex
        hexPulses = hex(int(pulses))[2:].upper()
        # pad with zeros
        hexPulses = hexPulses.zfill(num_bytes)
        # convert to bytes
        return hexPulses.encode('utf-8')

    def _bytes_to_radians(self, angle_bytes:bytes) -> float:
        ''' Converts a hexidecimal byte string to an angle in radians. '''
        # convert to bytes
        pulses = int(angle_bytes, 16)
        # convert to degrees
        deg = pulses / self._ppmu
        # convert to radians
        return np.deg2rad(deg)

    def _get_home_offset(self) -> int:
        ''' Get the home offset of the motor.
        
        Returns
        -------
        int
            The home offset of the motor, in pulses.
        '''
        resp = self._send_instruction(b'go', resp_len=11, require_resp_code=b'ho')[3:11]
        pos = int(resp[3:11], 16)
        # check negative
        if (pos >> 31) & 1:
            # negative number, take the two's compliment
            pos = -((pos ^ 0xffffffff) + 1)
        return pos

    def _set_hardware_home(self) -> float:
        ''' Sets the hardware home to be the current position.
        [WARNING: THIS WILL RESET HOME ON THE PHYSICAL HARDWARE. THIS CANNOT BE UNDONE, UNLESS YOU KNOW THE ORIGINAL HOME OFFSET.]

        Returns
        -------
        float
            The current position of the motor, in radians (should be zero or close to it).
        '''
        # get the position exactly
        pos_resp = self._send_instruction(b'gp', resp_len=11, require_resp_code=b'po')
        pos = int(pos_resp[3:11], 16)
        # check negative
        if (pos >> 31) & 1:
            # negative number, take the two's compliment
            pos = -((pos ^ 0xffffffff) + 1)
        # get the new offset including current offset
        new_offset = (self._get_home_offset() + pos) % self._travel

        # check negative
        if new_offset < 0:
            # negative number, take the two's compliment
            new_offset = -((new_offset ^ 0xffffffff) + 1)
        # encode the new offset
        new_offset_bytes = hex(new_offset)[2:].upper().encode('utf-8').zfill(8)
        # send the new offset
        self._send_instruction(b'so', data=new_offset_bytes)
        # check the new position
        return self._get_position()

    def _return_resp(self, resp:bytes) -> Union[float,None]:
        ''' Returns a response from the motor. Also checks if that response contains an error code, and alerts the user.
        
        Parameters
        ----------
        resp : bytes
            The response to return to the user.

        Returns
        -------
        float
            If the response was a position.
        0
            If the response was a nominal status.
        None
            If the response was a status.
        '''
        if resp[1:3] == b'GS': # status code
            # parse status
            s = self.get_status(resp)
            # return 0 if ok
            if s == 'ok': 
                return 0
            # otherwise, raise an error
            raise RuntimeError(f'{self} encountered status ({self.get_status(resp)})')
        elif resp[1:3] == b'PO':
            # return position
            return self._get_position(resp)
        else:
            # raise an error
            raise RuntimeError(f'{self} encountered an unexpected response ({resp}) which did not match any known response codes.')

    # +++ private overridden methods +++

    def _get_status(self, resp:bytes=None) -> str:
        ''' Retrieve the status of the motor. '''
        if resp is None:
            # get resp
            resp = self._send_instruction(b'gs', resp_len=5, require_resp_code=b'gs')
        # return the status
        if resp[3:5] in self.STATUS_CODES:
            return self.STATUS_CODES[resp[3:5]]
        else:
            return f'UNKNOWN STATUS CODE {resp[3:5]}'

    def _set_position(self, angle_radians:float) -> float:
        ''' Rotate the motor to an absolute position relative to home.

        Parameters
        ----------
        angle_radians : float
            The absolute angle to rotate to, in radians.
        
        Returns
        -------
        float
            The absolute position of the motor after the move, in radians.
        '''
        # request the move
        resp = self._send_instruction(b'ma', self._radians_to_bytes(angle_radians, num_bytes=8), resp_len=11)
        # block
        while self._is_active():
            pass
        # check response
        return self._return_resp(resp)

    def _move_relative(self, angle_radians:float) -> float:
        ''' Rotate the motor to a position relative to the current one.

        Parameters
        ----------
        angle_radians : float
            The angle to rotate, in radians.
        
        Returns
        -------
        float
            The ABSOLUTE angle in radians that the motor was moved to. Likely will not be the same as the angle requested.
        
        Returns
        -------
        float
            The absolute position of the motor after the move, in radians.
        '''
        # request the move
        resp = self._send_instruction(b'mr', self._radians_to_bytes(angle_radians, num_bytes=8))        # block
        while self._is_active():
            pass
        return self._return_resp(resp)

    def _is_active(self) -> bool:
        ''' Check if the motor is active by querying the status. '''
        resp = self._send_instruction(b'i1', resp_len=24, require_resp_code=b'i1')
        return resp[4] != 48 # zero in ASCII

    def _get_position(self, resp:bytes=None) -> float:
        ''' Get the current position of the motor in radians.
        
        Parameters
        ----------
        resp, optional
            The response from the device to parse. If none, device will be queried.
        
        Returns
        -------
        float
            The absolute position of the motor, in radians.
        '''
        # if no response is provided, query the device
        if resp is None:
            resp = self._send_instruction(b'gp', resp_len=11, require_resp_code=b'po')
        pos = resp[3:11]
        # check if negative and take the two's compliment
        pos = int(pos, 16)
        if (pos >> 31) & 1:
            # negative number, take the two's compliment
            pos = -((pos ^ 0xffffffff) + 1)
        # convert to radians
        return np.deg2rad(pos / self._ppmu)

class ThorLabsMotor:
    ''' ThorLabs Motor class.
    
    Parameters
    ----------
    name : str
        The unique name for the motor.
    serial_num : int
        The serial number of the motor.
    offset : float
        The offset of the motor, in radians. In other words, when the motor returns a position of zero, where does the actual motor hardware think it is?
    '''
    def __init__(self, name:str, serial_num:int, offset:float=0):
        # call super constructor
        super().__init__(name, 'ThorLabs', offset)

        # set attributes
        self.serial_num = serial_num
        self.motor_apt = apt.Motor(serial_num)

    # +++ overridden private methods +++

    def _get_status(self) -> int:
        ''' Returns 0 if nominal, anything else otherwise. '''
        return self.motor_apt.motion_error

    def _is_active(self) -> bool:
        ''' Returns true if the motor is actively moving, false otherwise. '''
        return self.motor_apt.is_in_motion

    def _rotate_relative(self, angle_radians:float) -> float:
        ''' Rotates the motor by a relative angle.

        Parameters
        ----------
        angle_radians : float
            The angle to rotate by, in radians.
        
        Returns
        -------
        float
            The absolute position of the motor after the move, in radians.
        '''
        # convert to degrees and send instruction
        angle = np.rad2deg(angle_radians)
        self.motor_apt.move_relative(angle)
        # (maybe) wait for move to finish
        while self._is_active():
            sleep(0.1)
        # return the position reached
        return self._get_position()

    def _rotate_absolute(self, angle_radians:float,) -> float:
        ''' Rotates the motor to an absolute angle.

        Parameters
        ----------
        angle_radians : float
            The angle to rotate by, in radians.
        
        Returns
        -------
        float
            The absolute position of the motor after the move, in radians.
        '''
        # convert to degrees and send instruction
        angle = np.rad2deg(angle_radians)
        self.motor_apt.move_to(angle)
        # (maybe) wait for move to finish
        while self._is_active():
            sleep(0.1)
        # return the current position
        return self._get_position()

    def _get_position(self) -> float:
        ''' Get the position of the motor.
        
        Returns
        -------
        float
            The position of the motor, in radians.
        '''
        # if we already know the position, just return it
        return np.deg2rad(self.motor_apt.position)

# +++ motor types dictionary +++
MOTOR_TYPES = {
    'ThorLabs': ThorLabsMotor,
    'Elliptec': ElliptecMotor
}
