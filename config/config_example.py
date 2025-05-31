#######################登录基础配置########################

API_ID = 11111
API_HASH = '1111111'
BOT_TOKEN = "脚本设定用botapi"
MY_NAME = 'dddd'    #  tg昵称榜单显示作用
NY_USERNAME = 'ssssss'   # tg 用户名
MY_TGID = 123344 # 自己的telegram id



########################运行代理配置########################

proxy_set = {
    'proxy_enable':True,#如果需要使用代理登录则设为true 反之False
    #tg登录的代理
    'proxy':{
        'scheme': 'socks5',  # "socks4", "socks5" and "http" are supported
        "hostname": '127.0.0.1',
        'port': 10801,
        'username': "",
        'password': ""
        },
    #网页访问用代理
    'PROXY_URL': 'http://127.0.0.1:10801'
}



PT_GROUP_ID = {
    "ZHUQUE_ID":-11111111,        #朱雀群ID
    "ZHUQUEBOCAI_ID":-111111111,  #朱雀菠菜群ID
    "SSD_ID":-11111111,           #SSD群ID
    "SSDPUBLIC_ID":-11111111,     #SSD公开群ID
    "HY_ID":-1111111111,          #红叶群ID
    "HYSTAFF_ID":-11111111,       #红叶二群ID 没有的话写和上面一个写一样ID（不可删除这个键名）
    "DOLBY_ID":-11111111,         #杜比群ID
    "AUDIENCES_ID":-1111111,      #观众群ID
    "BOT_MESSAGE_CHAT":MY_TGID,   #本脚本bot提示消息发送群 如果设置了群ID 则需要把bot加入对应的群 然后设为管理员，如果例设定 MY_TGID 则bot直接和个人私发
}


###################################auto_lotttery配置#############################

#参与抽奖的群组
LOTTERY_TARGET_GROUP = [
    PT_GROUP_ID['ZHUQUE_ID'],
    PT_GROUP_ID['DOLBY_ID'],
    PT_GROUP_ID['HY_ID'],
    PT_GROUP_ID['HYSTAFF_ID'],
    PT_GROUP_ID['SSD_ID'],
    PT_GROUP_ID['AUDIENCES_ID']
]
#参与抽奖的奖品
PRIZE_LIST = {
    "ZHUQUE_ID":['灵石','零食','LS'],            
    "DOLBY_ID":['鲸币','🐳币','JB'],
    "SSD_ID":['茉莉'],
    "AUDIENCES_ID":['爆米花'],
    "PTclub":['猫粮'],
    "HHclub":['憨豆'],
    "Test_ID":['test']
}   #设置需要参数的奖品名 暂不支持修改新增key




################################数据库配置##############################


DB_INFO = {
    "dbset":"mySQL", #mySQL/SQLite
    "address":"111.111.1.11", #mySQL数据库的IP地址 前面docker安装的mysql如果是bridge/host则同宿主ip
    "db_name":"数据库名称",    #mySQL数据库命名 对应安装数据库时的设定
    "port":3306,               #数据库端口  看安装时的映射
    "user":"用户名",            #数据用户名 root 或者安装时设定的username
    "password":"密码"           #对应用户名的密码
}







