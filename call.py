import serial
import time
import os

time.sleep(10)

def at(port, cmd):
    """执行 AT 命令返回结果"""
    port.write(cmd.encode(encoding='ascii') + b'\r')
    time.sleep(1)
    lines = []
    while port.in_waiting > 0:
        result = port.read(port.in_waiting)
        if result != b'':
            result = result.decode(encoding='ascii')
            lines += [l for l in result.split('\r\n') if l != '']
        else:
            break
    return lines

def upload_file(port, file_path):
    """上传音频文件到 SIM800"""
    # 先检查文件存在不存在，存在了就跳过
    file_name = os.path.basename(file_path)
    result = at(port, 'AT+FSLS=C:\\')
    if file_name in result:
        return
    with open(file_path, 'rb') as src:
        file_content = src.read()
        file_size = len(file_content)
        print('Creating audio file...')
        result = at(port, 'AT+FSCREATE={0}'.format(file_name))
        if (not result) or (result[0] != 'OK'):
            print('RESULT=', result)
            raise IOError('Failed to create file')
        print('Writing audio file [filename={0}, size={1}] ...'.format(file_name, file_size))
        at_cmd = 'AT+FSWRITE={0},0,{1},10'.format(file_name, file_size)
        print(at_cmd)
        result = at(port, at_cmd)
        print('>>>>>>>>>>>>>>>>>>>', result)
        if result and result[0] == '>': 
            print('Uploading file content...')
            port.write(file_content)
            print('File content uploaded')
        else:
            raise IOError('Failed to write file content')

COM_PORT = '/dev/ttyAMA0'

# 打开串口
with serial.Serial(COM_PORT, baudrate=115200, timeout=5) as port:

    if port.isOpen():
        print(port.name + ' is open...!!!')

    result = at(port, 'ATE0') # 关闭回显，同时测试连接情况
    if result[0] != 'OK':
        print('Failed to execute ATE0, check connection please.')
    print('>>>', result)

    upload_file(port, './to_play.amr')
    print('-----------------------------')
    print(at(port, 'AT+FSLS=C:\\')) # 检查是否上传成功

    print(at(port, 'AT+COLP=1'))

    print(at(port, 'ATD139XXXXXXXX;'))  # 139XXXXXXX 改成要拨打的手机号

    # 等待对方摘机
    while True:
        result = port.read(port.in_waiting)
        if result != b'':
            lines = result.decode(encoding='ascii')
            print('ATD>', lines)
            break

    time.sleep(3)
    at(port, 'AT+CREC=4,"C:\\to_play.amr",0,90')

    print('All done.')
