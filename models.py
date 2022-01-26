from django.db import models
import mongoengine
from mongoengine import *
# 使用 MongoEngine 0.8或者更高版本，对象和querysets具有to_json()方法。
    
class Liaodata(mongoengine.Document):
    userid= mongoengine.IntField(default=0)
    
    username=mongoengine.StringField(max_length=999)
    #注意，这里的username是聊天对方名，懒得修改了。
    leixing=mongoengine.IntField(default=0)
    
    zongshu= mongoengine.IntField(default=0)#
    jishu= mongoengine.IntField(default=0)
    createtime = mongoengine.DateTimeField()
    freshtime = mongoengine.DateTimeField()
    
class Liaolist(mongoengine.Document):
    userid0= mongoengine.IntField(default=0)
    userid1= mongoengine.IntField(default=0)
    username=mongoengine.StringField(max_length=999)
    leixing=mongoengine.IntField(default=0)
    fystatus=mongoengine.StringField(max_length=9)
    
    huifuid=mongoengine.IntField(default=0)
    huifuname=mongoengine.StringField(max_length=99)
    
    zhid=mongoengine.IntField(default=0)
    zhititle=mongoengine.StringField(max_length=99)
    zhitype=mongoengine.StringField(max_length=99)
    
    taidu=mongoengine.StringField(max_length=9)
    fy=mongoengine.StringField(max_length=999)
    fyshen=mongoengine.StringField(max_length=999)
    fyshu=mongoengine.IntField(default=0)
    createtime = mongoengine.DateTimeField()
    shentime=mongoengine.DateTimeField()

    
class Alljishu(mongoengine.Document):
    keyid= mongoengine.IntField(default=999)
    yonghu = mongoengine.IntField(default=0)
    yonghu1 = mongoengine.IntField(default=0)
    yonghu2 = mongoengine.IntField(default=0)
    biaoqian= mongoengine.IntField(default=0)
    qunzu = mongoengine.IntField(default=0)
    wenji=mongoengine.IntField(default=0)
    fayan=mongoengine.IntField(default=0)
    fuyan=mongoengine.IntField(default=0)
    wenduan=mongoengine.IntField(default=0)
    #此数据表只有一个记录，就是keyid为999，只能在终端中修改各种值

    
class Tongji(mongoengine.Document):
    tjid = mongoengine.IntField()
    
    # 这是指这个元素有几个附件
    dianji = mongoengine.IntField(default=0)
    guanzhu = mongoengine.IntField(default=0)
    fenxiang = mongoengine.IntField(default=0)
    biaoqian = mongoengine.IntField(default=0)#这是知识点加入几个标签的计数
    pinglun = mongoengine.IntField(default=0)
    tucao = mongoengine.IntField(default=0)#这是评论中吐槽的计数
    guanlian = mongoengine.IntField(default=0)
    maodun = mongoengine.IntField(default=0)#这是关联中矛盾的计数
    xiugai = mongoengine.IntField(default=0)
    neihan = mongoengine.IntField(default=0)#这是标签内含的内容的计数
    updatetime = mongoengine.DateTimeField()
    liaofreshtime = mongoengine.DateTimeField()
    #这是用户上一次登陆的时间，和标签，群组里最新变动的时间
    #最新更新时间，用于标签，数集，用户上次登陆时间，用户上次登陆时间，是在用户登陆时先读取，然后再写入更新
    zengwenji= mongoengine.IntField(default=0)
    zengbiaoqian= mongoengine.IntField(default=0)
    zengqunzu= mongoengine.IntField(default=0)
    zengfayan= mongoengine.IntField(default=0)
    shenfayan= mongoengine.IntField(default=0)
    zengfenxiang= mongoengine.IntField(default=0)
    #暂时不用
    fujian = mongoengine.IntField(default=0)#暂时不用
    chuan_yhid= mongoengine.StringField(max_length=999)#暂时不用
    chuan_qzid= mongoengine.StringField(max_length=999)#暂时不用
    chuan_zhid= mongoengine.StringField(max_length=999)#暂时不用
    chuan= mongoengine.StringField(max_length=99999)#暂时不用
    
    resouci = ListField(StringField(max_length=300))



# 这里记录了用户各类行为（关注，分享，加入标签，关联，评论，加入群组，用户被关注,用户关注等。
class Caozuo(models.Model):
    czid = models.AutoField(primary_key = True)
    cztype =  models.CharField(max_length=99,null=True)
    fy = models.TextField(max_length=9999,null=True)
    fytype = models.CharField(max_length=19,null=True)#这是用于表示发言类型：简讯还是求助的功能
    fyatt = models.CharField(max_length=19,null=True)
    fystatus = models.CharField(max_length=9,default="正在审核")
    fyfanwei = models.IntegerField(default=90000000)
    fymi = models.IntegerField(default=0) #这是发言的字数，代表密文的类型，0-明文，非零密文
    
    id0 = models.IntegerField(null=True)
    id1 = models.IntegerField(null=True)
    title0 = models.CharField(max_length=999,null=True)
    title1 = models.CharField(max_length=999,null=True)
    type0 =  models.CharField(max_length=19,null=True)
    type1 =  models.CharField(max_length=19,null=True)

    uid0 = models.IntegerField(null=True)#这是记录用户不论匿名与否的真实id
    uid1 = models.IntegerField(null=True)#这是用来表示匿名90000000
    uname = models.CharField(max_length=99,null=True)
    time0 = models.DateTimeField(null=True)#这是用户操作的原始时间
    time1 = models.DateTimeField(null=True)#这是审核通过的时间
    
    ding = models.IntegerField(default=0)
    cai = models.IntegerField(default=0)
    hui = models.IntegerField(default=0)
    
    fyhui= models.TextField(max_length=9999,null=True)
    #这是为了展示被回复的对象，如果是一大串发言文字的话
    
    fyshen= models.TextField(max_length=9999,null=True)
    #这是等待审核的明文
    fujianshu= models.IntegerField(default=0)
    
    def __str__(self):
        return self.czid
        
    # class Meta:
    #     model = Caozuo
    #     fields = ('time0', 'time1')
  
    
    
    
class Yonghu(models.Model):
    yonghu_id = models.AutoField(primary_key = True)
    # AutoField的同时，要在数据库管理终端上设置自增
    yonghu_name = models.CharField(max_length=99)
    yonghu_pswd = models.TextField(max_length=999,default="qwer1234")

    yonghu_status = models.CharField(max_length=9,default="正在审核")
    yonghu_type = models.CharField(max_length=9,default="普通用户")
    yonghu_touxiang= models.IntegerField(default=0)
    yonghu_gongkai= models.IntegerField(default=3)#这是用户公开多长时间的状态信息

    yonghu_area = models.CharField(max_length=99,null=True)
    yonghu_job = models.CharField(max_length=99,null=True)
    yonghu_contact = models.CharField(max_length=99,null=True)
    yonghu_hobby = models.CharField(max_length=99,null=True)
    yonghu_remark = models.CharField(max_length=99,null=True)
    yonghu_borntime = models.DateTimeField(null=True)
    
    # 以下是历史人物特有的信息
    yonghu_life = models.TextField(max_length=999,null=True)
    yonghu_born = models.CharField(max_length=99,null=True)#这是用于表示用户的生卒
    yonghu_fresh =  models.DateTimeField(null=True)#这是用于用户更新信息的时间,用来在审核页面排序
    
    def __str__(self):
        return self.yonghu_id

class Wenji(models.Model):
    wj_id = models.AutoField(primary_key = True)
    wj_title = models.CharField(max_length=99,null=True)
    wj_remark = models.TextField(max_length=999,default="无")

    wj_borntime = models.DateField(null=True)
    wj_deadtime = models.DateField(null=True)

    wj_status = models.CharField(max_length=9,default="正常有效")
    wj_type =  models.CharField(max_length=9,null=True)
    wj_yuanwen= models.IntegerField(default=0)
    wj_wdlist=models.IntegerField(default=0)#作废，与下面的wj_wdshu功能重复
    wj_wdshu=models.IntegerField(default=0)

    wj_fanwei = models.IntegerField(default=99999999)

    wj_area = models.CharField(max_length=99,null=True)
    wj_hangye = models.CharField(max_length=99,null=True)
    wj_publisher = models.CharField(max_length=99,null=True)

    wj_createrid = models.IntegerField(null=True)
    wj_creatername = models.CharField(max_length=99,null=True)
    wj_createtime = models.DateTimeField(null=True)
    wj_manager = models.IntegerField(null=True)

    fu = models.IntegerField(default=0)

    def __str__(self):
        return self.wj_title

class Wenduan(models.Model):
    wd_id = models.AutoField(primary_key = True)
    wd_title = models.CharField(max_length=99,null=True)
    wd_content = models.TextField(max_length=999,null=True)

    wj_id = models.IntegerField(null=True)
    wj_title = models.CharField(max_length=99,null=True)
    wj_xuhao = models.IntegerField(null=True)

    wd_status = models.CharField(max_length=9,default="正常有效")
    wd_type = models.CharField(max_length=9,default="暂无分类")
    # 这个wd8是指独立文段。
    wd_fanwei = models.IntegerField(default=90000000)

    wd_createrid = models.IntegerField(null=True)
    wd_creatername = models.CharField(max_length=99,null=True)
    wd_createtime = models.DateTimeField(null=True)
    wd_manager = models.IntegerField(null=True)
    
    fu = models.IntegerField(default=0)

    def __str__(self):
        return self.wd_title

class Biaoqian(models.Model):
    bq_id = models.AutoField(primary_key = True)
    bq_title = models.CharField(max_length=99,null=True)
    bq_remark = models.TextField(max_length=999,default="无")

    bq_status = models.CharField(max_length=9,default="正常有效")
    bq_fanwei = models.IntegerField(default=99999999)
    bq_type =  models.CharField(max_length=9,null=True)

    bq_createrid = models.IntegerField(null=True)
    bq_creatername = models.CharField(max_length=99,null=True)
    bq_createtime = models.DateTimeField(null=True)
    bq_manager = models.IntegerField(null=True)
    
    fu = models.IntegerField(default=0)

    def __str__(self):
        return self.bq_title


class Qunzu(models.Model):
    qz_id = models.AutoField(primary_key = True)
    qz_title = models.CharField(max_length=99,null=True)
    qz_remark = models.TextField(max_length=999,default="无")

    qz_status = models.CharField(max_length=9,default="正常有效")
    qz_type =  models.CharField(max_length=9,null=True)
    qz_join = models.CharField(max_length=9,default="qz")#作废不用
    qz_kouling = models.CharField(max_length=99,null=True)

    qz_createrid = models.IntegerField(null=True)
    qz_creatername = models.CharField(max_length=99,null=True)
    qz_createtime = models.DateTimeField(null=True)
    qz_manager = models.IntegerField(null=True)

    fu = models.IntegerField(default=0)

    def __str__(self):
        return self.qz_title


# 这里的fu_id是100000001，s4是被删除。f0是指文辑的原文档。f1指文辑的表格。f2指各类知识点的压缩包类型的附件。f3是指附图jpg，gif等。
class Fujian(models.Model):
    fu_id = models.AutoField(primary_key = True)
    fu_title = models.CharField(max_length=99,null=True)
    fu_status = models.CharField(max_length=9,default="正常有效")
    fu_type = models.CharField(max_length=9,null=True)
    item_id = models.IntegerField(null=True)
    fu_createrid = models.IntegerField(null=True)
    fu_createtime = models.DateTimeField(null=True)
    
    def __str__(self):
        return self.fu_id
        
        
        
        
        
        
#该模型废止，并入caozuo表中
class Fayanmima(models.Model):
    mi_hint = models.CharField(max_length=99,null=True)
    mi_status = models.CharField(max_length=9,default="正在审核")
    mi = models.CharField(max_length=99,null=True)
    mi_createid = models.IntegerField(null=True)
    mi_createtime = models.DateTimeField(null=True)

    def __str__(self):
        return self.mi_hint
        
        
        
        
# class Shuji(models.Model):
#     sji_id = models.AutoField(primary_key = True)
#     sji_title = models.CharField(max_length=99,null=True)
#     sji_remark = models.CharField(max_length=999,null=True)

#     sji_borntime = models.DateField(null=True)
#     sji_deadtime = models.DateField(null=True)

#     sji_status = models.CharField(max_length=9,default="正在审核")
#     sji_type =  models.CharField(max_length=9,null=True)
#     sji_fanwei = models.IntegerField(default=99999999)

#     sji_area = models.CharField(max_length=99,null=True)
#     sji_hangye = models.CharField(max_length=99,null=True)
#     sji_publisher = models.CharField(max_length=99,null=True)

#     sji_createrid = models.IntegerField(null=True)
#     sji_creatername = models.CharField(max_length=99,null=True)
#     sji_createtime = models.DateTimeField(null=True)
#     sji_manager = models.IntegerField(null=True)
    
#     fu = models.IntegerField(default=0)

#     def __str__(self):
#         return self.sji_title
        
        
# class Shuju(models.Model):
#     sju_id = models.AutoField(primary_key = True)
#     sju_value = models.FloatField(max_length=99,null=True)
#     sju_unit = models.CharField(max_length=999,null=True)
#     sju_serial = models.CharField(max_length=999,null=True)
#     sju_remark = models.CharField(max_length=999,null=True)

#     sji_id = models.IntegerField(null=True)
#     sji_title = models.CharField(max_length=99,null=True)

#     sju_status = models.CharField(max_length=9,default="正在审核")
#     sju_type = models.CharField(max_length=9,default="sju0")
#     sju_fanwei = models.IntegerField(default=99999999)

#     sju_createrid = models.IntegerField(null=True)
#     sju_creatername = models.CharField(max_length=99,null=True)
#     sju_createtime = models.DateTimeField(null=True)
#     sju_manager = models.IntegerField(null=True)
    
#     fu = models.IntegerField(default=0)

#     def __str__(self):
#         return self.sju_id
        
        
# class Gonggao(models.Model):
#     gonggao_content = models.CharField(max_length=999,null=True)
#     gg_createid = models.IntegerField(null=True)
#     gg_createtime = models.DateTimeField(null=True)
#     gg_status = models.CharField(max_length=9,default="正在审核")
#     gg_zishu=models.IntegerField(null=True)

#     def __str__(self):
#         return self.gg_createid

# class News(mongoengine.Document):
#     news_comm_id = mongoengine.IntField()
#     news_comm_content = mongoengine.StringField()
#     news_type = mongoengine.StringField()
#     news_status = mongoengine.StringField()
#     news_attitude = mongoengine.StringField()
#     news_fanwei= mongoengine.IntField()
#     news_zishu= mongoengine.IntField()
#     #这里news_tixing用于标记是否为密文，如果是则为原文的字数，如果不是则为零

#     item0_id=mongoengine.IntField()
#     item0_type=mongoengine.StringField()
#     item0_title= mongoengine.StringField()
#     item1_id=mongoengine.IntField()
#     item1_type=mongoengine.StringField()
#     item1_title= mongoengine.StringField()

#     fujian= mongoengine.IntField()
#     # 仅对于发言，要统计附件数显示在页面上
#     createrid = mongoengine.IntField()
#     creatername = mongoengine.StringField()
#     create_time = mongoengine.DateTimeField()

#     meta = {
#         'ordering': ['-create_time']
#     }
    
    
    
# # 这里记录了用户各类行为（关注，分享，加入标签，关联，评论，加入群组，用户被关注,用户关注等。
# class Yonghuaction(models.Model):
#     act_id = models.AutoField(primary_key = True)
#     act_fuyan = models.CharField(max_length=9999,default="无。")
# #这里fuyan的字符初始设置很大，是为了保存密文。

#     item0_id = models.IntegerField(null=True)
#     item0_title = models.CharField(max_length=999,null=True)
#     item0_type =  models.CharField(max_length=11,null=True)
#     item1_id = models.IntegerField(null=True)
#     item1_title = models.CharField(max_length=999,null=True)
#     item1_type =  models.CharField(max_length=11,null=True)

#     act_status = models.CharField(max_length=9,default="正在审核")
#     act_type =  models.CharField(max_length=9,null=True)
#     act_att =  models.CharField(max_length=19,default="att0")
#     act_fanwei = models.IntegerField(default=90000000)
    
#     act_fuyanzishu = models.IntegerField(default=0) 
#     #这里原是用于提醒的功能，现在用于标记是否是密文发布，如果是密，则记录为密文的字数，如果不是秘闻，则为0
    
#     act_createrid = models.IntegerField(null=True)
#     act_creatername = models.CharField(max_length=99,null=True)
#     act_createtime = models.DateTimeField(null=True)
    
#     fuyan_ding = models.IntegerField(default=0)
#     fuyan_cai = models.IntegerField(default=0)
    
#     def __str__(self):
#         return self.act_id


# class Fayan(models.Model):
#     fy_id = models.AutoField(primary_key = True)
#     fy_content = models.CharField(max_length=9999,null=True)
# #这里fuyan的字符初始设置很大，是为了保存密文。
#     fy_status = models.CharField(max_length=9,null=True)
#     fy_type =  models.CharField(max_length=9,null=True)
#     fy_fanwei = models.IntegerField(default=90000000)
#     fy_att = models.CharField(max_length=19,null=True)
#     fy_zishu= models.IntegerField(default=0) 
#     #这里原是用于提醒的功能，现在用于标记是否是密文发布，如果是密，则记录为密文的字数，如果不是秘闻，则为0


#     fy_createrid = models.IntegerField(null=True)
#     fy_creatername = models.CharField(max_length=99,null=True)
#     fy_createtime = models.DateTimeField(null=True)

#     fu= models.IntegerField(default=0)

#     def __str__(self):
#         return self.fy_id





