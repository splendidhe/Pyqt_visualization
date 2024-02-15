# Pyqt_visualization
使用pyqt实现数据可视化与3D模型的交互  

  **显示效果：**
![](GUI_icon/image.png)

## 打包命令
打包后运行会报错找不到模型文件，需要手动将model文件复制入dist\main\_internal路径下
### 第一版软件
```
pyinstaller -w -i .\GUI_icon\main_icon.ico  .\main.py
```
### 第二版软件
```
pyinstaller -w -i .\GUI_icon\main_icon.ico  .\spark.py
```

# 可视化方案第二版
##  3D模型的显示
![](GUI_icon/image-1.png)

##  数据可视化
![](GUI_icon/image-2.png)

## 地图定位
![](GUI_icon/image-3.png)

## 视频传输
![](GUI_icon/image-4.png)