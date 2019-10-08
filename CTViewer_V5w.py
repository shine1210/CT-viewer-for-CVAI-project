# from PyQt5 import QtWidgets
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox,QInputDialog,QLineEdit

import viewer_v6,sys
import numpy as np
import vtk
from cv2 import imread,cvtColor,COLOR_BGR2RGB,addWeighted
from os import execl,listdir
from scipy.io import loadmat

from h5py import File

from tkinter.filedialog import askdirectory,askopenfilename
from tkinter import Tk

class ViewerWindow(viewer_v6.Ui_MainWindow):

    def __init__(self,MainWindow):

        super().setupUi(MainWindow)

        self.CLOSE.clicked.connect(self.close)
        self.RESET.clicked.connect(self.restart_program)
        self.LOAD_DATA.clicked.connect(self.load_data)
        self.RENDER.clicked.connect(self.render)

        self.LOAD_MASK1.clicked.connect(self.load_mask_1R)
        self.LOAD_MASK2.clicked.connect(self.load_mask_2G)
        self.LOAD_MASK3.clicked.connect(self.load_mask_3B)

        self.image_slider.valueChanged.connect(self.ch_slice)
        self.state.setText('Welcome To CTViewer Ver3W')

    def ErrorMsg(self,input='INPUT TYPE ERROR'):
        msgBox = QMessageBox()
        msgBox.setWindowTitle('sysError')
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText(input)
        msgBox.setStandardButtons(QMessageBox.Retry)
        msgBox.setDefaultButton(QMessageBox.Retry)
        reply=msgBox.exec()

    # def getText(self):

    #     inputBox=QInputDialog()
    #     inputBox.setInputMode(0)
    #     inputBox.setTextEchoMode(QLineEdit.Normal)
    #     inputBox.setTextValue('')
    #     inputBox.setLabelText('Please Input MatFile Key')
    #     inputBox.setWindowTitle('MatFileKeyInputDialog')
    #     inputBox.setOkButtonText(u'Ok')
    #     inputBox.setCancelButtonText(u'Cancel')
    #     if inputBox.exec_() and inputBox.textValue()!='':
    #         return inputBox.textValue()
    #     else:
    #         self.ErrorMsg(input='Please Input MatFile Key')
    #         pass
    #     app.exec_()
    def getText(self,matdata):
        inputBox=QInputDialog()
        inputBox.setInputMode(0)
        inputBox.setWindowTitle('MatFileKeyInputDialog')
        itemlist=list()
        for key in matdata.keys():
            itemlist.append(key)
        inputBox.setComboBoxItems(itemlist)
        inputBox.setComboBoxEditable(False)
        inputBox.setLabelText('Please Input MatFile Key')
        inputBox.setOkButtonText(u'Ok')
        inputBox.setCancelButtonText(u'Cancel')
        if inputBox.exec_() and inputBox.textValue()!='':
            return inputBox.textValue()

    def input_type(self):
        if self.TDM_CHECK.isChecked()==True:
            return 'TYPE_TDM'
        elif self.IMAGE_CHECK.isChecked()==True:
            return 'TYPE_IMAGE'

    def mask_type(self):
        if self.IMASK_SET.isChecked()==True:
            return 'TYPE_MASK_IMG'
        elif self.NPY_CHECK.isChecked()==True:
            return 'TYPE_NPY'
        elif self.MAT_CHECK.isChecked()==True:
            return 'TYPE_MAT'

    def NormlizDcm(self,dicom_set):

        self.state.setText('Normalizing')
        dcm_float=dicom_set.astype(np.float)
        dcm_uint8=np.zeros(dicom_set.shape,np.uint8)

        dcm_float[dcm_float>600]=600
        dcm_float[dcm_float<-200]=-200
        dcm_float[:,:,:]=255*((dcm_float[:,:,:]-dcm_float.min())/(dcm_float.max()-dcm_float.min()))
        dcm_uint8[:,:,:]=dcm_float[:,:,:]

        return dcm_uint8


    def load_data(self):

        self.state.setText('Loading Data')

        type=self.input_type()
        global height,width,bytesPerComponent,bytesPerLine

        if type=='TYPE_IMAGE':

            global file_list,fille_path

            
            root=Tk()
            root.withdraw()
            
            fille_path=askdirectory()
            try:
                file_list=listdir(fille_path)
            except FileNotFoundError:
                flag=False
            except ValueError:
                flag=False
                self.ErrorMsg()
            else:
                flag=True
            if flag==False:
                pass
            else:
                file_list=listdir(fille_path)

                file_list.sort(key=lambda x:int(x[1:-4]))

                # self.listWidget.addItems(file_list)

                image_path=fille_path+'/'+file_list[0]
                img=imread(image_path)

                height,width,bytesPerComponent=img.shape
                bytesPerLine=3*width
                cvtColor(img,COLOR_BGR2RGB,img)

                QImg=QImage(img.data,width,height,bytesPerLine,QImage.Format_RGB888) 
                pixmap=QPixmap.fromImage(QImg)
                self.OG_IMAGE.setPixmap(pixmap)
                self.OG_IMAGE.setScaledContents(True)

                self.MASK_IMAGE.setPixmap(pixmap)
                self.MASK_IMAGE.setScaledContents(True)

                self.image_slider.setMinimum(0)
                self.image_slider.setMaximum(len(file_list)-1)

                self.state.setText('Done')

        elif type=='TYPE_TDM':

            global dcm_nor
            root=Tk()
            root.withdraw()
            fille_path=askopenfilename()

            try:
                TDM_data=loadmat(fille_path)
            except FileNotFoundError:
                flag=False
            except ValueError:
                self.ErrorMsg()
                flag=False
            except NotImplementedError:
            	flag='v73'
            else:
                flag=True
            if flag==False:
                pass

            elif flag=='v73':
                TDM_data=File(fille_path)
                TDMKey=self.getText(TDM_data)
                try:
                    TDM_image_set=TDM_data[TDMKey]
                except KeyError:
                    self.ErrorMsg(input='No Tag Name TDM')
                    flag=False
                if flag==False:
                    pass
                else:
                	TDM_image_v=TDM_data[TDMKey]
                	TDM_image_set=np.transpose(TDM_image_v[()])
                	dcm_nor=self.NormlizDcm(TDM_image_set)

            else:
                TDM_data=loadmat(fille_path)
                TDMKey=self.getText(TDM_data)
                try:
                    TDM_image_set=TDM_data[TDMKey]
                except KeyError:
                    self.ErrorMsg(input='No Tag Name TDM')
                    flag=False
                if flag==False:
                    pass
                else:
                    TDM_image_set=TDM_data[TDMKey]
                    dcm_nor=self.NormlizDcm(TDM_image_set)

            img=np.zeros((dcm_nor.shape[0],dcm_nor.shape[1],3),np.uint8)

            img[:,:,0]=dcm_nor[:,:,0]
            img[:,:,1]=dcm_nor[:,:,0]
            img[:,:,2]=dcm_nor[:,:,0]

            height,width,bytesPerComponent=img.shape
            bytesPerLine=3*width

            QImg=QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap=QPixmap.fromImage(QImg)
            self.OG_IMAGE.setPixmap(pixmap)
            self.OG_IMAGE.setScaledContents(True)

            self.MASK_IMAGE.setPixmap(pixmap)
            self.MASK_IMAGE.setScaledContents(True)

            self.image_slider.setMinimum(0)
            self.image_slider.setMaximum(dcm_nor.shape[2]-1)

            self.state.setText('Done')


    def load_mask_1R(self):

        self.state.setText('Loading Mask')

        mtype=self.mask_type()

        if mtype=='TYPE_MASK_IMG':
            global fille_path_mask_R,file_list_mask_R

            root=Tk()
            root.withdraw()
            fille_path_mask_R=askdirectory()
            try:
                file_list_mask_R=listdir(fille_path_mask_R)
            except FileNotFoundError:
                flag=False
            else:
                flag=True

            if flag==False:
                pass
            else:
                file_list_mask_R=listdir(fille_path_mask_R)
                file_list_mask_R.sort(key=lambda x:int(x[1:-4]))
                # self.listWidget.addItems(file_list_mask)

                self.state.setText('Done')

        elif mtype=='TYPE_NPY':
            global npy_mask_data_R

            root=Tk()
            root.withdraw()
            fille_path_mask_R=askopenfilename()

            try:
                npy_mask_data_R=np.load(fille_path_mask_R)
            except FileNotFoundError:
                flag=False
            except OSError:
                self.ErrorMsg()
                flag=False
            else:
                flag=True

            if flag==False:
                pass
            else:
                npy_mask_data_R=np.load(fille_path_mask_R)
                self.state.setText('Done')

        elif mtype=='TYPE_MAT':
            global mat_mask_data_R

            root=Tk()
            root.withdraw()
            fille_path_mask_R=askopenfilename()

            try:
                mat_mask_R=loadmat(fille_path_mask_R)
            except FileNotFoundError:
                flag=False
            except OSError:
                self.ErrorMsg()
                flag=False
            except ValueError:
                self.ErrorMsg()
                flag=False
            except NameError:
                self.ErrorMsg()
                flag=False
            except NotImplementedError:
                flag='v73'
            else:
                flag=True

            if flag==False:
                pass
            elif flag=='v73':
                mat_mask_R=File(fille_path_mask_R)
                maskKey=self.getText(mat_mask_R)
                try:
                    mat_mask_data_R=mat_mask_R[maskKey]
                except KeyError:
                    self.ErrorMsg(input='No Tag Name Mask')
                    flag=False
                except TypeError:
                    self.ErrorMsg(input='No Tag Name Mask')
                    flag=False
                if flag==False:
                    pass
                else:
                    mat_mask_data_v=mat_mask_R[maskKey]
                    mat_mask_data_R=np.transpose(mat_mask_data_v[()])
                    self.state.setText('Done')
            else:
                mat_mask_R=loadmat(fille_path_mask_R)
                maskKey=self.getText(mat_mask_R)
                try:
                    mat_mask_data_R=mat_mask_R[maskKey]
                except KeyError:
                    self.ErrorMsg(input='No Tag Name Mask')
                    flag=False
                if flag==False:
                    pass
                else:
                    mat_mask_data_R=mat_mask_R[maskKey]
                    self.state.setText('Done')

    def load_mask_2G(self):

        self.state.setText('Loading Mask')

        mtype=self.mask_type()

        if mtype=='TYPE_MASK_IMG':
            global fille_path_mask_G,file_list_mask_G

            root=Tk()
            root.withdraw()
            fille_path_mask_G=askdirectory()
            try:
                file_list_mask_G=listdir(fille_path_mask_G)
            except FileNotFoundError:
                flag=False
            else:
                flag=True

            if flag==False:
                pass
            else:
                file_list_mask_G=listdir(fille_path_mask_G)
                file_list_mask_G.sort(key=lambda x:int(x[1:-4]))
                # self.listWidget.addItems(file_list_mask)
                self.state.setText('Done')

        elif mtype=='TYPE_NPY':
            global npy_mask_data_G

            root=Tk()
            root.withdraw()
            fille_path_mask_G=askopenfilename()

            try:
                npy_mask_data_G=np.load(fille_path_mask_G)
            except FileNotFoundError:
                flag=False
            except OSError:
                self.ErrorMsg()
                flag=False
            else:
                flag=True

            if flag==False:
                pass
            else:
                npy_mask_data_G=np.load(fille_path_mask_G)
                self.state.setText('Done')

        elif mtype=='TYPE_MAT':
            global mat_mask_data_G

            root=Tk()
            root.withdraw()
            fille_path_mask_G=askopenfilename()

            try:
                mat_mask_G=loadmat(fille_path_mask_G)
            except FileNotFoundError:
                flag=False
            except OSError:
                self.ErrorMsg()
                flag=False
            except ValueError:
                self.ErrorMsg()
                flag=False
            except NameError:
                self.ErrorMsg()
                flag=False
            except NotImplementedError:
                flag='v73'
            else:
                flag=True

            if flag==False:
                pass
            elif flag=='v73':
                mat_mask_G=File(fille_path_mask_G)
                maskKey=self.getText(mat_mask_G)
                try:
                    mat_mask_data_G=mat_mask_G[maskKey]
                except KeyError:
                    self.ErrorMsg(input='No Tag Name Mask')
                    flag=False
                except TypeError:
                    self.ErrorMsg(input='No Tag Name Mask')
                    flag=False
                if flag==False:
                    pass
                else:
                    mat_mask_data_v=mat_mask_G[maskKey]
                    mat_mask_data_G=np.transpose(mat_mask_data_v[()])
                    self.state.setText('Done')
            else:
                mat_mask_G=loadmat(fille_path_mask_G)
                maskKey=self.getText(mat_mask_G)
                try:
                    mat_mask_data_G=mat_mask_G[maskKey]
                except KeyError:
                    self.ErrorMsg(input='No Tag Name Mask')
                    flag=False
                if flag==False:
                    pass
                else:

                    mat_mask_data_G=mat_mask_G[maskKey]
                    self.state.setText('Done')

    def load_mask_3B(self):

        self.state.setText('Loading Mask')
        mtype=self.mask_type()

        if mtype=='TYPE_MASK_IMG':
            global fille_path_mask_B,file_list_mask_B

            root=Tk()
            root.withdraw()
            fille_path_mask_B=askdirectory()
            try:
                file_list_mask_B=listdir(fille_path_mask_B)
            except FileNotFoundError:
                flag=False
            else:
                flag=True

            if flag==False:
                pass

            else:
                file_list_mask_B=listdir(fille_path_mask_B)
                file_list_mask_B.sort(key=lambda x:int(x[1:-4]))
                # self.listWidget.addItems(file_list_mask)
                self.state.setText('Done')

        elif mtype=='TYPE_NPY':
            global npy_mask_data_B

            root=Tk()
            root.withdraw()
            fille_path_mask_B=askopenfilename()

            try:
                npy_mask_data_B=np.load(fille_path_mask_B)
            except FileNotFoundError:
                flag=False
            except OSError:
                self.ErrorMsg()
                flag=False
            else:
                flag=True

            if flag==False:
                pass
            else:
                npy_mask_data_B=np.load(fille_path_mask_B)
                self.state.setText('Done')

        elif mtype=='TYPE_MAT':
            global mat_mask_data_B

            root=Tk()
            root.withdraw()
            fille_path_mask_B=askopenfilename()

            try:
                mat_mask_B=loadmat(fille_path_mask_B)
            except FileNotFoundError:
                flag=False
            except ValueError:
                self.ErrorMsg()
                flag=False
            except OSError:
                self.ErrorMsg()
                flag=False
            except NameError:
                self.ErrorMsg()
                flag=False
            except NotImplementedError:
                flag='v73'
            else:
                flag=True

            if flag==False:
                pass
            elif flag=='v73':
                mat_mask_B=File(fille_path_mask_B)
                maskKey=self.getText(mat_mask_B)
                try:
                    mat_mask_data_B=mat_mask_B[maskKey]
                except KeyError:
                    self.ErrorMsg(input='No Tag Name Mask')
                    flag=False
                except TypeError:
                    self.ErrorMsg(input='No Tag Name Mask')
                    flag=False
                if flag==False:
                    pass
                else:
                    mat_mask_data_v=mat_mask_B[maskKey]
                    mat_mask_data_B=np.transpose(mat_mask_data_v[()])
                    self.state.setText('Done')
            else:
                mat_mask_B=loadmat(fille_path_mask_B)
                maskKey=self.getText(mat_mask_B)
                try:
                    mat_mask_data_B=mat_mask_B[maskKey]
                except KeyError:
                    self.ErrorMsg(input='No Tag Name Mask')
                    flag=False
                if flag==False:
                    pass
                else:

                    mat_mask_data_B=mat_mask_B[maskKey]
                    self.state.setText('Done')

        
    def mask_1R(self,mask_nums):

        mtype=self.mask_type()
        if mtype=='TYPE_MASK_IMG':
            try:
                file_list_mask_R
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                return np.zeros((height,width,bytesPerComponent),np.uint8)
            else:

                mask_path=fille_path_mask_R+'/'+file_list_mask_R[mask_nums]
                mask=imread(mask_path,0)

                mask_rgb=np.zeros((height,width,bytesPerComponent),np.uint8)
                mask_rgb[:,:,2]=mask
                return mask_rgb

        elif mtype=='TYPE_NPY':
            try:
                npy_mask_data_R
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                return np.zeros((height,width,bytesPerComponent),np.uint8)
            else:

                mask_temp=np.zeros((height,width),np.uint8)
                mask_rgb=np.zeros((height,width,bytesPerComponent),np.uint8)
                mask_temp[:,:]=npy_mask_data_R[:,:,mask_nums]
                mask_rgb[:,:,2]=mask_temp*255
                return mask_rgb

        elif mtype=='TYPE_MAT':
            try:
                mat_mask_data_R
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                return np.zeros((height,width,bytesPerComponent),np.uint8)
            else:

                mask_rgb=np.zeros((height,width,bytesPerComponent),np.uint8)
                mask_rgb[:,:,2]=mat_mask_data_R[:,:,mask_nums]

                return mask_rgb

    def mask_2G(self,mask_nums):

        mtype=self.mask_type()
        if mtype=='TYPE_MASK_IMG':
            try:
                file_list_mask_G
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                return np.zeros((512,512,3),np.uint8)
            else:

                mask_path=fille_path_mask_G+'/'+file_list_mask_G[mask_nums]
                mask=imread(mask_path,0)

                mask_rgb=np.zeros((height,width,bytesPerComponent),np.uint8)
                mask_rgb[:,:,1]=mask
                return mask_rgb

        elif mtype=='TYPE_NPY':
            try:
                npy_mask_data_G
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                return np.zeros((height,width,bytesPerComponent),np.uint8)
            else:

                mask_temp=np.zeros((height,width),np.uint8)
                mask_rgb=np.zeros((height,width,bytesPerComponent),np.uint8)
                mask_temp[:,:]=npy_mask_data_G[:,:,mask_nums]
                mask_rgb[:,:,1]=mask_temp
                return mask_rgb

        elif mtype=='TYPE_MAT':
            try:
                mat_mask_data_G
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                return np.zeros((height,width,bytesPerComponent),np.uint8)
            else:

                mask_rgb=np.zeros((height,width,bytesPerComponent),np.uint8)
                mask_rgb[:,:,1]=mat_mask_data_G[:,:,mask_nums]

                return mask_rgb

    def mask_3B(self,mask_nums):

        mtype=self.mask_type()
        if mtype=='TYPE_MASK_IMG':
            try:
                file_list_mask_B
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                return np.zeros((height,width,bytesPerComponent),np.uint8)
            else:

                mask_path=fille_path_mask_B+'/'+file_list_mask_B[mask_nums]
                mask=imread(mask_path,0)

                mask_rgb=np.zeros((height,width,bytesPerComponent),np.uint8)
                mask_rgb[:,:,0]=mask
                return mask_rgb

        elif mtype=='TYPE_NPY':
            try:
                npy_mask_data_B
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                return np.zeros((height,width,bytesPerComponent),np.uint8)
            else:

                mask_temp=np.zeros((height,width),np.uint8)
                mask_rgb=np.zeros((height,width,bytesPerComponent),np.uint8)
                mask_temp[:,:]=npy_mask_data_B[:,:,mask_nums]
                mask_rgb[:,:,0]=mask_temp
                return mask_rgb

        elif mtype=='TYPE_MAT':
            try:
                mat_mask_data_B
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                return np.zeros((height,width,bytesPerComponent),np.uint8)
            else:

                mask_rgb=np.zeros((height,width,bytesPerComponent),np.uint8)
                mask_rgb[:,:,0]=mat_mask_data_B[:,:,mask_nums]

                return mask_rgb

    def ch_slice(self,value):

        type=self.input_type()

        if type=='TYPE_IMAGE':
            try:
                file_list
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                pass
            else:

                slice_num=self.image_slider.value()
                #print(slice_num)

                image_path=fille_path+'/'+file_list[slice_num]
                img=imread(image_path)

                height,width,bytesPerComponent=img.shape
                bytesPerLine=3*width

                mask_r=self.mask_1R(len(file_list)-1-slice_num)
                mask_g=self.mask_2G(len(file_list)-1-slice_num)
                mask_b=self.mask_3B(len(file_list)-1-slice_num)

                img_over=addWeighted(img,1.0,mask_r, 1.0, 0)
                img_over=addWeighted(img_over,1.0,mask_g, 1.0, 0)
                img_over=addWeighted(img_over,1.0,mask_b, 1.0, 0)

                cvtColor(img,COLOR_BGR2RGB,img)
                cvtColor(img_over,COLOR_BGR2RGB,img_over)
                
                QImg=QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
                pixmap=QPixmap.fromImage(QImg)
                self.OG_IMAGE.setPixmap(pixmap)
                self.OG_IMAGE.setScaledContents(True)

                QImg_over=QImage(img_over.data, width, height, bytesPerLine, QImage.Format_RGB888)
                pixmap_over=QPixmap.fromImage(QImg_over)
                self.MASK_IMAGE.setPixmap(pixmap_over)
                self.MASK_IMAGE.setScaledContents(True)

                numb_of_slic='number of slice : '+str(slice_num)
                self.state.setText(numb_of_slic)

        elif type=='TYPE_TDM':

            try:
                dcm_nor
            except NameError:
                flag=False
            else:
                flag=True

            if flag==False:
                pass
            else:

                slice_num=self.image_slider.value()
                img=np.zeros((dcm_nor.shape[0],dcm_nor.shape[1],3),np.uint8)

                img[:,:,0]=dcm_nor[:,:,slice_num]
                img[:,:,1]=dcm_nor[:,:,slice_num]
                img[:,:,2]=dcm_nor[:,:,slice_num]

                height,width,bytesPerComponent=img.shape
                bytesPerLine=3*width

                mask_r=self.mask_1R(slice_num)
                mask_g=self.mask_2G(slice_num)
                mask_b=self.mask_3B(slice_num)

                # print(mask_r.max())

                img_over=img.copy()

                img_over[:,:,2][mask_r[:,:,2]!=0]=255
                img_over[:,:,1][mask_r[:,:,2]!=0]=0
                img_over[:,:,0][mask_r[:,:,2]!=0]=0

                img_over[:,:,1][mask_g[:,:,1]!=0]=255
                img_over[:,:,2][mask_g[:,:,1]!=0]=0
                img_over[:,:,0][mask_g[:,:,1]!=0]=0

                img_over[:,:,0][mask_b[:,:,0]!=0]=255
                img_over[:,:,2][mask_b[:,:,0]!=0]=0
                img_over[:,:,1][mask_b[:,:,0]!=0]=0
                # img_over=add(img,mask_r)
                # img_over=add(img_over,mask_g)
                # img_over=add(img_over,mask_b)

                cvtColor(img,COLOR_BGR2RGB,img)
                cvtColor(img_over,COLOR_BGR2RGB,img_over)

                QImg=QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
                pixmap=QPixmap.fromImage(QImg)
                self.OG_IMAGE.setPixmap(pixmap)
                self.OG_IMAGE.setScaledContents(True)

                QImg_over=QImage(img_over.data, width, height, bytesPerLine, QImage.Format_RGB888)
                pixmap_over=QPixmap.fromImage(QImg_over)
                self.MASK_IMAGE.setPixmap(pixmap_over)
                self.MASK_IMAGE.setScaledContents(True)

                numb_of_slic='number of slice : '+str(slice_num)
                self.state.setText(numb_of_slic)

    def render(self):

            try:
                mat_mask_data_R
            except NameError:
                pass
            else:
                mR=mat_mask_data_R*50

                pred_mask=mR
                data_matrix=pred_mask.astype(np.uint8)
                m,n,z=data_matrix.shape
                # data_matrix[data_matrix>0.5]=50
                vtk.vtkObject.GlobalWarningDisplayOff()

                dataImporter = vtk.vtkImageImport()

                data_string = data_matrix.tostring()
                dataImporter.CopyImportVoidPointer(data_string, len(data_string))

                dataImporter.SetDataScalarTypeToUnsignedChar()
                dataImporter.SetNumberOfScalarComponents(1)

                dataImporter.SetDataExtent(0, z-1, 0, n-1, 0, m-1)
                dataImporter.SetWholeExtent(0, z-1, 0, n-1, 0, m-1)

                alphaChannelFunc = vtk.vtkPiecewiseFunction()
                alphaChannelFunc.AddPoint(0, 0.0)
                alphaChannelFunc.AddPoint(50, 0.5)
                alphaChannelFunc.AddPoint(150, 0.5)

                colorFunc = vtk.vtkColorTransferFunction()
                colorFunc.AddRGBPoint(0, 0.0, 0.0, 0.0)
                colorFunc.AddRGBPoint(50, 1.0, 0.0, 0.0)
                colorFunc.AddRGBPoint(150, 0.0, 0.0, 1.0)

                volumeProperty = vtk.vtkVolumeProperty()
                volumeProperty.SetColor(colorFunc)
                volumeProperty.SetScalarOpacity(alphaChannelFunc)

                compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()

                volumeMapper = vtk.vtkVolumeRayCastMapper()
                volumeMapper.SetVolumeRayCastFunction(compositeFunction)
                volumeMapper.SetInputConnection(dataImporter.GetOutputPort())

                volume = vtk.vtkVolume()
                volume.SetMapper(volumeMapper)
                volume.SetProperty(volumeProperty)

                renderer = vtk.vtkRenderer()
                renderWin = vtk.vtkRenderWindow()
                renderWin.AddRenderer(renderer)
                renderInteractor = vtk.vtkRenderWindowInteractor()
                renderInteractor.SetRenderWindow(renderWin)

                renderer.AddVolume(volume)

                renderer.SetBackground(1, 1, 1)
                renderWin.SetSize(400, 400)

                def exitCheck(obj, event):
                    if obj.GetEventPending() != 0:
                        obj.SetAbortRender(1)

                renderWin.AddObserver("AbortCheckEvent", exitCheck)

                renderInteractor.Initialize()
                renderWin.Render()
                renderWin.SetWindowName('3D Vessal')
                renderInteractor.Start()

    def restart_program(self):
        python = sys.executable
        execl(python, python, * sys.argv)

        # QtWidgets.QApplication.exit(ViewerWindow.EXIT_CODE_REBOOT)

        # self.OG_IMAGE.clear()
        # self.MASK_IMAGE.clear()
        # for name in dir():
        #   if not name.startswith('_'):
        #       del globals()[name]
        # self.__clear_env()


    def close(self):
        sys.modules[__name__].__dict__.clear()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = ViewerWindow(MainWindow)
    MainWindow.setWindowTitle('CTViewer Ver3W')

    MainWindow.show()
    sys.exit(app.exec_())

# if __name__ == "__main__":

    # currentExitCode = ViewerWindow.EXIT_CODE_REBOOT

    # while currentExitCode == ViewerWindow.EXIT_CODE_REBOOT:
    #     app = QtWidgets.QApplication(sys.argv)
    #     MainWindow = QtWidgets.QMainWindow()
    #     ui = ViewerWindow(MainWindow)
    #     MainWindow.show()
    #     currentExitCode=app.exec_()
    #     app=None

