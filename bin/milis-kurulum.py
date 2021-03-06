#!/usr/bin/python3

# Milis Linux Konsol / Grafik Kurulum Betiği
# Not: Bu betik henüz tamamlanmış değil. 
# Commit tarihi: 25.09.2016 
# Dialog manuali için: http://pythondialog.sourceforge.net/doc/

import os,sys,re,subprocess,time
import crypt

os.system("mps -GG")
if os.path.exists("/usr/bin/pip3") is False:
	os.system("mps -G")
	time.sleep(3)
	os.system("mps kur python3-pip && pip3 install pythondialog")
if os.path.exists("/usr/bin/acp") is False:
	os.system("mps -G")
	time.sleep(3)
	os.system("mps kur advcp")
#lsb-release tamiri
time.sleep(3)
os.system("mps -sz lsb-release && mps -ik lsb-release")

from dialog import Dialog

d = Dialog(dialog="dialog")
f = open("/tmp/log.txt","w")

def runShellCommand(c):
	out = subprocess.check_output(c,stderr=subprocess.STDOUT,shell=True,universal_newlines=True)
	return out.replace("\b","")  #encode byte format to string, ugly hack 

def greetingDialog():
	status = d.yesno(title="Milis Linux'a hoş geldiniz !", 
	text="Tanıtım yazısı buraya gelecek...\n\n\n\nKuruluma devam etmek istiyor musunuz ?",width=70,height=10)
	if status == "ok":
		checkUsername()
	else:
		sys.exit()

def checkUsername():
	
	#status ok ya da cancel gibi durumları çekiyor. 
	status,username = d.inputbox(text="Lütfen kullanıcı adı giriniz")
	
	#NAME_REGEX bkz. man 5 adduser.conf
	if bool(re.compile(r'^[a-z][-a-z0-9]*$').match(username)):
		checkUserPassword(username)
	else:
		status=d.msgbox(text="Hatalı kullanıcı adı girdiniz.\n\n\
		Kullanıcı adları alfanümerik karakterle başlamalıdır\
		ve alfanümerik (A-Z), nümerik (0-9) ve tire (-) \
		harici bir karakter içermemelidir.",width=60)
		if status == "ok":
			checkUsername()


def createUser(name,username,password):
    #encPass = crypt.crypt(password,"22")   
    #os.system("useradd -p "+encPass+ " -s "+ "/bin/bash "+ "-d "+ "/home/" + username+ " -m "+ " -c \""+ name+"\" " + username)
	os.system("kopar milis-"+name+" "+username)
	os.system('echo -e "'+password+'\n'+password+'" | passwd '+username)

def checkUserPassword(username):
	#insecure=True parolanın yıldız şeklinde gözükmesini sağlar, 
	#root şifresi sorarken belki bunu silebiliriz normal sudo şifresi 
	#girer gibi gözükmez. 
	status,password = d.passwordbox(text="Lütfen {} kullanıcısı için şifrenizi giriniz".format(username),insecure=True)
	if len(password) > 0:
		createUser(username,username,password)
		f.write("[+] Kullanıcı eklendi")
		d.infobox(text=username+" kullanıcısı başarıyla eklendi.")
		if d.yesno(text="Yeni kullanıcı eklemek istiyor musunuz ?") == "ok":
			checkUsername()
		else:
			chooseDisk()
	else:
		status=d.msgbox(text="Şifreniz boş olamaz")
		checkUserPassword(username)

def chooseDisk():
	diskChoice = []
	diskNames  = runShellCommand("lsblk -nS -o NAME").split('\n')
	diskModels = runShellCommand("lsblk -nS -o MODEL").split('\n')
	for i in range(len(diskNames)):
		diskChoice.append((diskNames[i],diskModels[i]))
	status,selectedDisk = d.menu(text="Lütfen bölümleme yapmak istediğiniz diski seçiniz:",choices=diskChoice)
	os.system("cfdisk /dev/" + selectedDisk)
	choosePart()

def choosePart():
	partChoice = []
	validParts = ['sd','hd','mmcblk0p']
	#Şimdilik Parted kütüphanesine gerek kalmadı, lsblk istediğimiz bütün değerleri alıyor.
	diskParts  = runShellCommand("lsblk -ln -o  NAME    | awk '{print $1}'").split('\n')
	partSizes  = runShellCommand("lsblk -ln -o  SIZE    | awk '{print $1}'").split('\n')
	partFs     = runShellCommand("lsblk -ln -o  FSTYPE  | awk '{print $1}'").split('\n')
	partMajmin = runShellCommand("lsblk -ln -o  MAJ:MIN | awk '{print $1}'").split('\n')
	partLabel  = runShellCommand("lsblk -ln -o  LABEL").split('\n') #Bunda awk yok çünkü arada boşluk olabilir. 
	for i in range(len(diskParts)-1):
		if partMajmin[i].split(":")[1] != "0": # partition olmayanları ele (sda/sdb seçince grub bozuluyor.)
			for validPart in validParts:
				if validPart in diskParts[i]: 
					partChoice.append((diskParts[i],partLabel[i]+ "\t" +partSizes[i]+"\t"+partFs[i]))
	status,selectedPart = d.menu(text="Sistemin kurulacağı diski seçiniz",choices=partChoice)
	if status == "ok":
		f.write("{} seçildi !".format(selectedPart)) #burası da düzeltilcek şimdilik böyle commitliyorum :D
		print("{} seçildi !".format(selectedPart))
		formatDialog(selectedPart)
def formatDialog(part):
	status = d.yesno(title="Uyarı !", 
	text="/dev/{} bölümü ext4 türünde formatlanacak. Emin misiniz ?".format(part))	
	if status == "ok":
		d.infobox(text="Formatlanıyor... Lütfen bekleyiniz...")
		formatPart(part)
		time.sleep(5)
	else:
		choosePart() 
		
def formatPart(part):
	hedef="/dev/"+part
	os.system("umount "+hedef)
	os.system("mkfs.ext4 "+hedef)
	d.infobox(text="/dev/"+part+" Disk Formatlandı")
	chooseSwap(part)
	hedefBagla(hedef)

def hedefBagla(hedef):
	os.system("mount "+hedef+" /mnt")
	d.infobox(text="hedef disk bağlandı.")
	sistemKopyala(hedef)

def sistemKopyala(hedef):
	os.system("clear")
	#print("\033c")
	os.system("acp -g -axnu /  /mnt")
	#os.system("cp -axvnu /  /mnt")
	initrdOlustur(hedef)
	
def initrdOlustur(hedef):
	os.system("mount --bind /dev /mnt/dev")
	os.system("mount --bind /sys /mnt/sys")
	os.system("mount --bind /proc /mnt/proc")
	os.system('chroot /mnt dracut --no-hostonly --add-drivers "ahci" -f /boot/initramfs')
	if d.yesno(text="Grub kurmak istiyor musunuz ?") == "ok":
		grubKur(hedef)
	else:
		kurulumBitir()

def grubKur(hedef):
	hedef = hedef[:-1]
	if hedef == "/dev/mmcblk0": #SD kart'a kurulum fix
		os.system("grub-install --boot-directory=/mnt/boot /dev/mmcblk0")
	else:
		os.system("grub-install --boot-directory=/mnt/boot " + hedef)
	os.system("chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg")
	kurulumBitir()
	
def kurulumBitir():
	d.infobox(text="milis işletim sistemi kuruldu.")
		
def chooseSwap(part):
	swapChoice = []
	validParts = ['sd','hd','mmcblk0p']
	#Şimdilik Parted kütüphanesine gerek kalmadı, lsblk istediğimiz bütün değerleri alıyor.
	diskParts  = runShellCommand("lsblk -ln -o  NAME    | awk '{print $1}'").split('\n')
	partSizes  = runShellCommand("lsblk -ln -o  SIZE    | awk '{print $1}'").split('\n')
	partFs     = runShellCommand("lsblk -ln -o  FSTYPE  | awk '{print $1}'").split('\n')
	partMajmin = runShellCommand("lsblk -ln -o  MAJ:MIN | awk '{print $1}'").split('\n')
	partLabel  = runShellCommand("lsblk -ln -o  LABEL").split('\n') #Bunda awk yok çünkü arada boşluk olabilir. 
	for i in range(len(diskParts)-1):
		if partMajmin[i].split(":")[1] != "0": # partition olmayanları ele (sda/sdb swap için uygun değil)
			if diskParts[i] != part:
				for validPart in validParts: 
					if validPart in diskParts[i]: #loop partlar gibi swap kurulamayacak alanları ele
						swapChoice.append((diskParts[i],partLabel[i]+ "\t" +partSizes[i]+"\t"+partFs[i]))
	status,selectedPart = d.menu(text="Takas alanının yer alacağı disk bölümünü seçiniz",choices=swapChoice)
	if status == "ok":
		f.write("{} seçildi !".format(selectedPart)) #burası da düzeltilcek şimdilik böyle commitliyorum :D
		print("{} seçildi !".format(selectedPart))		
		setSwap(selectedPart)
		
def setSwap(part):
	os.system("mkswap "+"/dev/"+part)
	os.system('echo "`lsblk -ln -o UUID /dev/' + part + '` none swap sw 0 0" | tee -a /etc/fstab')
	
		 
if __name__ == "__main__":

	greetingDialog()
