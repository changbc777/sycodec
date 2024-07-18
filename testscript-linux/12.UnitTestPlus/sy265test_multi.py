import os
import time
import threading

def run_cmd(cmds):
	global curthread
	for cmd in cmds:
		print('runing: ' + cmd)
		os.system(cmd)
	curthread = curthread -1

if __name__ == '__main__':
	sycodepath = '' # code
	videopath = '' # code
	
	x265path = 'x265' # result
	sy265path = 'sy265' # result
	
	x265codec = 'encoder/x265' # encoder
	sy265codec = 'encoder/sy265' # encoder
	ffmpegcodec = 'encoder/ffmpeg' # encoder

	# param
	video_class = ['6']
	QP_LOW = [12, 17, 22, 27]
	QP_NORMAL = [22, 27, 32, 37]
	QP_HIGH = [32, 37, 42, 47]
	QP = []
	test_low_qp = 1
	test_normal_qp = 1
	test_high_qp = 1
	sy265_param = '--preset fast --tune psnr --keyint 256 --bframes 15 --rc-lookahead 64 --frame-threads 8'
	x265_param = '--preset fast --tune psnr --keyint 256 --bframes 15 --rc-lookahead 64 --frame-threads 8'
	keyintSec = 0
	testssim = 1
	testvmafneg = 0
	testCPUPercent = 1
	maxthread = 1

	# video setting
	needscale = 0
	scaleto = 720
	needfps = 0
	fpsto = 20

	# test setting
	testx265 = 1
	testsy265anchor = 1
	testsy265tools = 1
	tools_sy265 = []
	tools_x265 = []

	# sy265tools
	tools_sy265.append('-aq 2')

	# x265 tools
	tools_x265.append('--preset veryslow --bframes 3 --rc-lookahead 16')
	
	# export
	# os.environ["LD_LIBRARY_PATH"] += ':' + sycodepath + '/WestLake/3rdparty/opencv-4.6.0/lib64'
	# cmd = 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:' + sycodepath + '/WestLake/3rdparty/opencv-4.6.0/lib64'
	#print(cmd)
	#os.system(cmd)

	# set test QP
	if(test_low_qp):
		QP.extend(QP_LOW)
	if(test_normal_qp):
		QP.extend(QP_NORMAL)
	if(test_high_qp):
		QP.extend(QP_HIGH)
	QP = list(set(QP))
	QP.sort()
	print(QP)

	# creat result dir
	if not os.exists(x265path):
		os.makedirs(x265path)
	if not os.exists(sy265path):
		os.makedirs(sy265_path)

	# creat tools
	with open('%s/tools' % (x265path), 'w') as f:
		for tools in tools_x265:
			f.write(tools+'\n')
	with open('%s/tools' % (sy265path), 'w') as f:
		for tools in tools_sy265:
			f.write(tools+'\n')

	# calculate cpu percent
	if(testCPUPercent):
		sy265codec = '/usr/bin/time -v ' + sy265codec
		x265codec = '/usr/bin/time -v ' + x265codec

	# used for multithread task
	tasks = []

	for curClass in video_class:
		file = open('list')
		line = file.readline()
		testCurClass = 0
		while line:
			line = line.replace('\n', '')
			lines = line.split()
			if(lines[0]=='Class'):
				testCurClass = 0
				if(curClass==lines[1]):
					testCurClass = 1
					videopath = lines[2]
				line = file.readline()
				continue
			if(not testCurClass):
				line = file.readline()
				continue
			inputfile = videopath + '/' + lines[0]
			width = lines[1]
			height = lines[2]
			fps = lines[3]
			print(inputfile)
			print(width)
			print(height)
			print(fps)
			keyint = int(fps)*keyintSec
			yuv_fmt = ' -s %s*%s -r %s ' %(width, height, fps)

			# scale
			if(needscale):
				if(int(width) < int(height)):
					scalewidth = scaleto
					scaleheight = int(int(width) * int(height) / scaleto)
				else:
					scaleheight = scaleto
					scalewidth = int(int(width) * int(height) / scaleto)
				cmd = '%s %s -theads 8 -i %s/%s.yuv -r %s -s %s*%s -y scale.yuv'\
				%(ffmpegcodec, yuv_fmt, videopath, lines[0], str(fps), str(scalewidth), str(scaleheight))
				print(cmd)
				os.system(cmd)
				width = str(scalewidth)
				height = str(scaleheight)
				yuv_fmt = '-s %s*%s -r %s -pix_fmt yuv420p' %(str(width), str(height), str(fps))
			if(needscale):
				inputyuv = 'scale.yuv'
			else:
				inputyuv = '%s/%s.yuv' %(videopath, lines[0])
			if(needfps):
				cmd = '%s %s -threads 8 -i %s -r %s -y fps.yuv' \ 
				%(ffmpegcodec, yuv_fmt, inputyuv, str(fpsto))
				print(cmd)
				os.system(cmd)
				inputyuv = 'fps.yuv'
				fps = fpsto
				yuv_fmt = '-s %s*%s -r %s -pix_fmt yuv420p' %(str(width), str(height), str(fps))

			# test x265
			if(testx265):
				for q in QP:
					cmds = []
					cmd = '%s --input %s --input-res %sx%s --fps %s --keyint %s %s --crf %d -o %s/%s_%d.265 > %s/%s_%d.txt 2>&1'\
						%(x265codec, inputyuv, str(width), str(height),  str(fps), keyint, x265_param, q, x265_path, lines[0], q, x265_path, lines[0], q)
					cmds.append(cmd)
					cmd = '%s %s -threads 8 -i %s -r %s -threads 8 -i %s/%s_%d.265 -threads 8 -lavfi psnr -f null - > %s/%s_%d_psnr.txt 2>&1' \ 
					%(ffmpegcodec, yuv_fmt, inputyuv, str(fps), x265_path, lines[0], q, x265_path, lines[0], q)
					cmds.append(cmd)
					if(testssim):
						cmd = '%s %s -threads 8 -i %s -r %s -threads 8 -i %s/%s_%d.265 -threads 8 -lavfi ssim -f null - > %s/%s_%d_ssim.txt 2>&1' \ 
						%(ffmpegcodec, yuv_fmt, inputyuv, str(fps), x265_path, lines[0], q, x265_path, lines[0], q)
						cmds.append(cmd)
					if(testvmafneg):
						cmd = '%s -i %s/%s_%d.265 -pix_fmt yuv420p -y rec.yuv' \ 
						%(ffmpegcodec, x265_path, lines[0], q)
						cmds.append(cmd)
						cmd = 'vmaf -d rec.yuv -r %s -b 8 -w %s -h %s -p 420 -m path=vmaf_v0.6.1neg.json --threads 8 -o %s/%s_%s_vmaf.txt' \
						%(inputyuv, str(width), str(height), x265_path, lines[0], str(q))
						cmds.append(cmd)
					tasks.append(threading.Thread(target=run_cmd, args=(cmds,)))

					# test x265 for other tools
					toolfile = open('%s/tools' % (x265path))
					toolline = toolfile.readline()
					while toolline:
						toolline = toolline.replace('\n', '')
						toolname = toolline.replace(' ', '_')
						toolname = toolname.replace('-','')
						toolpath = x265_path+'/'+toolname
						if not os.path.exists(toolpath):
							os.makedirs(toolpath)
						cmds=[]
						cmd = '%s --input %s --input-res %sx%s --fps %s --keyint %s %s --crf %d %s -o %s/%s_%d.265 > %s/%s_%d.txt 2>&1'\
						%(x265codec, inputyuv, str(width), str(height),  str(fps), keyint, x265_param, q, toolline, toolpath, lines[0], q, toolpath, lines[0], q)
						cmds.append(cmd)
						cmd = '%s %s -threads 8 -i %s -r %s -threads 8 -i %s/%s_%d.265 -threads 8 -lavfi psnr -f null - > %s/%s_%d_psnr.txt 2>&1' \ 
						%(ffmpegcodec, yuv_fmt, inputyuv, str(fps), toolpath, lines[0], q, toolpath, lines[0], q)
						cmds.append(cmd)
						if(testssim):
							cmd = '%s %s -threads 8 -i %s -r %s -threads 8 -i %s/%s_%d.265 -threads 8 -lavfi ssim -f null - > %s/%s_%d_ssim.txt 2>&1' \ 
							%(ffmpegcodec, yuv_fmt, inputyuv, str(fps), toolpath, lines[0], q, toolpath, lines[0], q)
							cmds.append(cmd)
						if(testvmafneg):
							cmd = '%s -i %s/%s_%d.265 -pix_fmt yuv420p -y rec.yuv' \ 
							%(ffmpegcodec, toolpath, lines[0], q)
							cmds.append(cmd)
							cmd = 'vmaf -d rec.yuv -r %s -b 8 -w %s -h %s -p 420 -m path=vmaf_v0.6.1neg.json --threads 8 -o %s/%s_%s_vmaf.txt' \
							%(inputyuv, str(width), str(height), toolpath, lines[0], str(q))
							cmds.append(cmd)
						tasks.append(threading.Thread(target=run_cmd, args=(cmds,)))
						toolline = toolfile.readline()


					
			# test sy265 anchor
			for q in QP:
				if(testsy265anchor):
					cmds = []
					cmd = '%s --input %s --input-res %sx%s --fps %s --keyint %s %s --crf %d -o %s/%s_%d.265 > %s/%s_%d.txt 2>&1'\
						%(sy265codec, inputyuv, str(width), str(height),  str(fps), keyint, sy265_param, q, sy265_path, lines[0], q, sy265_path, lines[0], q)
					cmds.append(cmd)
					cmd = '%s %s -threads 8 -i %s -r %s -threads 8 -i %s/%s_%d.265 -threads 8 -lavfi psnr -f null - > %s/%s_%d_psnr.txt 2>&1' \ 
					%(ffmpegcodec, yuv_fmt, inputyuv, str(fps), sy265_path, lines[0], q, sy265_path, lines[0], q)
					cmds.append(cmd)
					if(testssim):
						cmd = '%s %s -threads 8 -i %s -r %s -threads 8 -i %s/%s_%d.265 -threads 8 -lavfi ssim -f null - > %s/%s_%d_ssim.txt 2>&1' \ 
						%(ffmpegcodec, yuv_fmt, inputyuv, str(fps), sy265_path, lines[0], q, sy265_path, lines[0], q)
						cmds.append(cmd)
					if(testvmafneg):
						cmd = '%s -i %s/%s_%d.265 -pix_fmt yuv420p -y rec.yuv' \ 
						%(ffmpegcodec, sy265_path, lines[0], q)
						cmds.append(cmd)
						cmd = 'vmaf -d rec.yuv -r %s -b 8 -w %s -h %s -p 420 -m path=vmaf_v0.6.1neg.json --threads 8 -o %s/%s_%s_vmaf.txt' \
						%(inputyuv, str(width), str(height), sy265_path, lines[0], str(q))
						cmds.append(cmd)
					tasks.append(threading.Thread(target=run_cmd, args=(cmds,)))

					# test sy265 for other tools
					if(testsy265tools)
						toolfile = open('%s/tools' % (sy265_path))
						toolline = toolfile.readline()
						while toolline:
							toolline = toolline.replace('\n', '')
							toolname = toolline.replace(' ', '_')
							toolname = toolname.replace('-','')
							toolpath = sy265_path+'/'+toolname
							if not os.path.exists(toolpath):
								os.makedirs(toolpath)
							cmds=[]
							cmd = '%s --input %s --input-res %sx%s --fps %s --keyint %s %s --crf %d %s -o %s/%s_%d.265 > %s/%s_%d.txt 2>&1'\
							%(sy265codec, inputyuv, str(width), str(height),  str(fps), keyint, sy265_param, q, toolline, toolpath, lines[0], q, toolpath, lines[0], q)
							cmds.append(cmd)
							cmd = '%s %s -threads 8 -i %s -r %s -threads 8 -i %s/%s_%d.265 -threads 8 -lavfi psnr -f null - > %s/%s_%d_psnr.txt 2>&1' \ 
							%(ffmpegcodec, yuv_fmt, inputyuv, str(fps), toolpath, lines[0], q, toolpath, lines[0], q)
							cmds.append(cmd)
							if(testssim):
								cmd = '%s %s -threads 8 -i %s -r %s -threads 8 -i %s/%s_%d.265 -threads 8 -lavfi ssim -f null - > %s/%s_%d_ssim.txt 2>&1' \ 
								%(ffmpegcodec, yuv_fmt, inputyuv, str(fps), toolpath, lines[0], q, toolpath, lines[0], q)
								cmds.append(cmd)
							if(testvmafneg):
								cmd = '%s -i %s/%s_%d.265 -pix_fmt yuv420p -y rec.yuv' \ 
								%(ffmpegcodec, toolpath, lines[0], q)
								cmds.append(cmd)
								cmd = 'vmaf -d rec.yuv -r %s -b 8 -w %s -h %s -p 420 -m path=vmaf_v0.6.1neg.json --threads 8 -o %s/%s_%s_vmaf.txt' \
								%(inputyuv, str(width), str(height), toolpath, lines[0], str(q))
								cmds.append(cmd)
							tasks.append(threading.Thread(target=run_cmd, args=(cmds,)))
							toolline = toolfile.readline()
			line = file.readline()
		#multithread task
		global curthread
		curthread = 0
		for t in tasks:
			while(1):
				if(curthread < maxthread):
					curthread = curthread + 1
					t.start()
					break
				time.sleep(1)
		for t in mythreads:
			t.join()
		print('all tasks done')