# -*- encoding:utf-8 -*-


"""This scripts wraps-up the GMYC commandline codes in the form of pyQt5-GUI application"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import re
import sys, os
from PyQt5.uic import loadUiType
from GMYC import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import *
import time


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

FORM_CLASS, _= loadUiType("GM.ui")# use ui reference to load the widgets

class Main(QMainWindow, FORM_CLASS):    # create class instance
    def __init__(self):
        super(Main, self).__init__()
        self.setWindowIcon(QIcon(os.path.join('icons', 'GMYC.ico')))
        self.setupUi(self)
        self.Handel_Buttons()  # connect widget to method when triggered (clicked)
        quit = QAction("Quit", self)
        self.progress= QProgressBar()
        self.progress.setStyle(QStyleFactory.create("windows"))
        self.progress.setRange(0, 1)
        #self.statusBar().showMessage('No Jobs.....')
        #self.statusBar().showMessage('Message in statusbar.')
        self.statusBar.addWidget(self.progress)

        # quit.setIconVisibleInMenu(True)
        quit.triggered.connect(self.closeEvent)

    def closeEvent(self, event):

         close = QMessageBox.question(self, "QUIT", "Are you sure want to stop process?",QMessageBox.Yes | QMessageBox.No)
         if close == QMessageBox.Yes:

             event.accept()
             sys.exit(0)

         else:
             event.ignore()

    def Handel_Buttons(self):  # call back functions
        self.pushButton_7.clicked.connect(self.browse_file1)
        self.pushButton_2.clicked.connect(self.browse_file3)
        self.pushButton_3.clicked.connect(self.download)
        self.pushButton_4.clicked.connect(self.view)
        self.pushButton_5.clicked.connect(self.clear)



    def browse_file1(self):
        self.browse_file = QFileDialog.getOpenFileName(self, "browse file", directory=".",filter="All Files (*.*)")
        self.lineEdit_3.setText(QDir.toNativeSeparators(str(self.browse_file[0])))
        return self.browse_file[0]


    def browse_file3(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            self.lineEdit_2.setText(QDir.toNativeSeparators(str(filenames[0])))



    def download(self, tree, print_detail = True, show_tree = False, show_llh = True, show_lineages = True, print_species = True, print_species_spart = True, pv = 0.01, save_file= None):

        try:
            self.unique= str(int(time.time()))
            self.pushButton_3.setText('Please wait analysis is going on')
            self.progress.setRange(0, 0)
            open_file= self.lineEdit_3.text()
            save_file = self.lineEdit_2.text()
            treetest = open(open_file)
            l1 = treetest.readline()
            is_nexus = (l1.strip() == "#NEXUS")
            treetest.close()
            if is_nexus:
                nexus = NexusReader(open_file)
                nexus.blocks['trees'].detranslate()
                newick_tree = nexus.trees.trees[0]
                stree = newick_tree
                stree = newick_tree
            if not is_nexus:
                stree = open_file

            llh_list = []
            min_change = 0.1
            max_iters = 100
            best_llh = float("-inf")
            best_num_spe = -1
            best_node = None
            utree = um_tree(stree, open_file, self.unique)
            for tnode in utree.nodes:
                QApplication.processEvents()

                wt_list, num_spe = utree.get_waiting_times(threshold_node = tnode)
                tt = tree_time(wt_list, num_spe)
                last_llh = float("-inf")
                change = float("inf")
                cnt = 0

                while change > min_change and cnt < max_iters:
                    cnt = cnt + 1
                    para, nn, cc = fmin_l_bfgs_b(tar_fun, [1, 1], args = tuple([tt]), bounds = [[0, 10], [0, 10]], approx_grad = True)
                    #para, nn, cc = fmin_tnc(tar_fun, [0, 0], args = [tt], disp = False, bounds = [[0, 10], [0, 10]], approx_grad = True)
                    tt.update(para[0], para[1])
                    logl = tt.sum_llh()
                    change = abs(logl - last_llh)
                    last_llh = logl
                f= open(os.path.join(save_file, self.unique+ "result_details.txt"), "a")
                if print_detail:
                    print("Num spe:" + repr(num_spe) + ": " + repr(tt.sum_llh()), file= f)
                    print("spe_lambda:" + repr(tt.spe_rate), file= f)
                    print("coa_lambda:" + repr(tt.coa_rate), file= f)
                    print("spe_p:" + repr(tt.spe_p), file= f)
                    print("coa_p:" + repr(tt.coa_p), file= f)
                    print("-----------------------------------------------------", file= f)
                f.close()
                final_llh = tt.sum_llh()
                if final_llh > best_llh:
                    best_llh = final_llh
                    best_num_spe = num_spe
                    best_node = tnode
                llh_list.append(final_llh)

            null_logl = optimize_null_model(utree)

            wt_list, num_spe = utree.get_waiting_times(threshold_node = best_node)
            one_spe, spes = utree.get_species()
            lrt = lh_ratio_test(null_llh = null_logl, llh = best_llh, df = 2)
            p_value= round(lrt.get_p_value(), 5)
            print(p_value)

            file2= open(os.path.join(save_file, self.unique+"result_summary.txt"), "w+")
            print("Highest llh:" + repr(best_llh), file= file2)
            print("Num spe:" + repr(best_num_spe), file= file2)
            print("Null llh:" + repr(null_logl), file= file2)
            print("P-value:" + repr(lrt.get_p_value()), file= file2)
            file2.close()
            if show_lineages:
                utree.num_lineages(wt_list, save_file)

            if show_llh:
                plt.plot(llh_list)
                plt.ylabel('Log likelihood')
                plt.xlabel('Time')
                plt.savefig(os.path.join(save_file, self.unique+ "Likelihood.png"))


            if print_species:
                utree.print_species(save_file)

            if print_species_spart:

                utree.print_species_spart(save_file, p_value)

            if show_tree:
                utree.tree.show()
            else:
                utree.tree.render(os.path.join(save_file, self.unique+ "myoutput.png"))
                utree.tree.render(os.path.join(save_file, self.unique+ "myoutput.pdf"))

            self.pushButton_3.setText('Run analysis and save GMYC output')



        except Exception as e:
            print(e)
            self.progress.setRange(0, 1)
            #self.statusBar().clearMessage()
            self.pushButton_3.setText('Run analysis and save GMYC output')
            QMessageBox.warning(self, "Warning", f"The species demitation output not obtained, please check input file type because {e}")
            return
        QMessageBox.information(self, "Information", "The species delimitation output data generated successfully")
        self.pushButton_3.setText('Run analysis and save GMYC output')
        self.progress.setRange(0, 1)
        #self.statusBar().clearMessage()


    # def takeinputs(self):
    #     comment1, done1 = QInputDialog.getText(
    #          self, 'Input Dialog', 'Enter your first comment:')
    #     comment2, done2 = QInputDialog.getText(
    #        self, 'Input Dialog', 'Enter your second comment:')
    #     save_file= self.lineEdit_2.text()
    #     if done1 and done2:
    #
    #         try:
    #             fin = open(resource_path(os.path.join(save_file, "partition.spart")), "rt")
    #             data = fin.read()
    #             data = data.replace("this is my first comment", str(comment1))
    #             data = data.replace("this is my second comment", str(comment2))
    #             fin.close()
    #             fin = open(resource_path(os.path.join(save_file,  "partition.spart")), "wt")
    #             fin.write(data)
    #             fin.close()
    #
    #         except Exception:
    #             QMessageBox.warning(self, "Warning", "The spart file is not generated, please generate the output files")
    #             return
    #         QMessageBox.information(self, "Information", "The spart file is updated successfully")


    def view(self):
        try:
            save_file = self.lineEdit_2.text()
            pixmap = QPixmap(resource_path(os.path.join(save_file,  self.unique+ "myoutput.png")))
            f = open(resource_path(os.path.join(save_file, self.unique+ "partition.txt")), "rt")
            self.scene = QGraphicsScene()
            self.scene.addPixmap(QPixmap(pixmap))
            self.graphicsView_2.setScene(self.scene)
            self.scene_1 = QGraphicsScene()
            mytext1 = QGraphicsSimpleTextItem(f.read())
            self.scene_1.addItem(mytext1)
            self.graphicsView.setScene(self.scene_1)
            f.close()
        except Exception:
            QMessageBox.warning(self, "Warning", "The species delimitation view is not obtained, please genetrate the analysis output first")
            return
        QMessageBox.information(self, "Information", "The species delimitation result image and partition generated successfully")


    def clear(self):
        try:

            self.lineEdit_3.setText("")
            self.lineEdit_2.setText("")
            self.graphicsView_2.setScene(QGraphicsScene())
            self.graphicsView.setScene(QGraphicsScene())
        except Exception:
            QMessageBox.warning(self, "Warning", "The input data is not cleared, Please do manually")
            return
        QMessageBox.information(self, "Information", "Please start a new analysis")



def main1():

    app=QApplication(sys.argv)

    window=Main()
    window.show()
    app.exec_()



if __name__=='__main__':
    main1()
