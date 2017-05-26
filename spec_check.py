import matplotlib
matplotlib.use('TkAgg')

from spec_check_config import *

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
import pyfits as fits
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import sys
import os, fnmatch
import tkMessageBox

if sys.version_info[0] < 3:
    import Tkinter as tk
else:
    import tkinter as tk

from tkFileDialog import askdirectory, askopenfilename

# Create a new Matplotlib toolbar that does not display live x,y coordinates
# (this caused the toolbar to move around in its tk grid cell)
class my_toolbar(NavigationToolbar2TkAgg):
    toolitems = [t for t in NavigationToolbar2TkAgg.toolitems if
               t[0] in ('Pan', 'Zoom', 'Save')]
    def set_message(self, msg):
        pass


class ViewSpec(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        #Window Title
        self.master.wm_title('View Window')

        master.columnconfigure(0, weight=0)
        master.columnconfigure(2, weight=1)
        master.rowconfigure(5, weight=1)


        self.obsid=np.empty(10)

        #Number in list
        self.list_counter = 0

        #Check if list has been successfully loaded
        self.list_loaded = False


        # This overrides the command to exit a tkinter window using the red exit button on mac
        # and calls a custon quit command. Without this line, the embedded matplotlib canvas
        # would cause a fatal error in python
        self.master.protocol('WM_DELETE_WINDOW', self._quit)
        

       	#Cretae matplotlib canvas for viewing spectra
       	self.spec_fig, self.spec_ax = plt.subplots(1, figsize = (10,4))

        self.spec_canvas = FigureCanvasTkAgg(self.spec_fig, master=self.master)
        self.spec_canvas.get_tk_widget().grid(row=5,column=0, columnspan=20, rowspan=18, \
            sticky=tk.NSEW, pady=(0,50))

       	self.spec_fig.canvas.draw()

        #Create separate frame for matplotlib toolbar
        self.toolbar_frame = tk.Frame(self.master)
        self.toolbar_frame.grid(row=23,column=3, columnspan=5, rowspan=2, sticky='NE')
        self.beam_toolbar = my_toolbar(self.spec_canvas, self.toolbar_frame)
        self.beam_toolbar.update()

       	#Working directory input
       	self.wrk_dir = tk.StringVar()
       	self.wrk_dir_entry = tk.Entry(self.master, width=40, textvariable=self.wrk_dir)
       	self.wrk_dir_entry.grid(row= 0,column=4, sticky = 'NW', columnspan=9)
        self.wrk_dir_entry.insert(0, default_working_directory)
       	tk.Label(self.master, text='Working Directory').grid(row=0, column=3, \
       		sticky='NE', padx=(80,5))

       	#Browse button for working directory
       	self.browse_wrk_dir_button = tk.Button(self.master, text='Browse', \
       		command=self.browse_wrk_dir)
       	self.browse_wrk_dir_button.grid(row=0, column=13, sticky='NW', padx=(0,80))


       	#Entry for loading target list
       	self.target_list_loc = tk.StringVar()
       	self.target_list_loc_entry = tk.Entry(self.master, width=40, \
       		textvariable=self.target_list_loc)
       	self.target_list_loc_entry.grid(row=1, column=4, sticky='NW', columnspan=9)
        self.target_list_loc_entry.insert(0, default_target_list)
       	tk.Label(self.master, text='Target List').grid(row=1, column=3, \
       		sticky='NE', padx=(80,5))


        #Check button for overplotting 
        self.overplot_on = tk.IntVar()
        self.overplot_check = tk.Checkbutton(self.master, text = 'Overplotting', \
          variable = self.overplot_on, offvalue = 0, onvalue = 1)
        self.overplot_check.grid(row = 2, column = 12, sticky='NW')


       	#Browse button for target list
       	self.browse_target_list_button = tk.Button(self.master, text='Browse', \
       		command=self.browse_target_list)
       	self.browse_target_list_button.grid(row=1, column=13, sticky='NW')

        #Load button for target list
        self.load_list_button = tk.Button(self.master, text = 'Load List', \
          command = self.load_list)
        self.load_list_button.grid(row=2, column=13, sticky = 'NW')


        #Save output button
        self.save_button = tk.Button(self.master, text = 'Save Output', \
          command = self.save_output)
        self.save_button.grid(row = 4, column = 13, sticky = 'NW')

        #Display object info 
        tk.Label(self.master, text='Object ID: ').grid(row=0, column =0, sticky = 'NE')
        self.display_obsid = tk.Label(self.master, text = '', width = 15, anchor='w')
        self.display_obsid.grid(row=0, column=1, columnspan = 2, sticky='NW')

        tk.Label(self.master, text='Obs. Date: ').grid(row=1, column = 0, sticky = 'NE')
        self.display_obsdate = tk.Label(self.master, text = '', width = 15, anchor='w')
        self.display_obsdate.grid(row=1,column=1, columnspan = 2, sticky = 'NW')

        tk.Label(self.master, text='RA: ').grid(row=2, column=0, sticky = 'NE')
        self.display_RA = tk.Label(self.master, text = '', width = 15, anchor='w')
        self.display_RA.grid(row=2, column=1, columnspan=2, sticky='NW')

        tk.Label(self.master, text='DEC: ').grid(row=3, column=0, sticky = 'NE')
        self.display_DEC = tk.Label(self.master, text = '', width = 15, anchor='w')
        self.display_DEC.grid(row=3, column=1, columnspan=2, sticky='NW')


        #Entry for feature name
        self.feature_name = tk.StringVar()
        self.feature_entry = tk.Entry(self.master, width = 10, \
          textvariable=self.feature_name)
        self.feature_entry.grid(row=4, column=0, sticky='NE', pady=(10,0))
        self.feature_entry.insert(0, 'Feature Name')


        #Button for flagging features
        self.flag_button = tk.Button(self.master, text='Flag', width = 10, 
          command = self.flag_feature)
        self.flag_button.grid(row = 4, column=1, sticky = 'NW', pady=(10,0))

        #Flag display
        self.flag_display = tk.Label(self.master, text='')
        self.flag_display.grid(row=4, column = 2, sticky = 'NW', pady=(10,0))


       	#Wavelength entry
       	self.lower_wvl = tk.StringVar()
       	self.lower_wvl_entry = tk.Entry(self.master, width=7, \
       		textvariable=self.lower_wvl)
       	self.lower_wvl_entry.grid(row=23, column = 0, sticky = 'NW', padx=(80,5))
        self.lower_wvl_entry.insert(0, str(default_low_wvl))

       	tk.Label(self.master, text='Lower').grid(row=24, column=0, sticky = 'NE', padx=(0,35))


       	self.upper_wvl = tk.StringVar()
       	self.upper_wvl_entry = tk.Entry(self.master, width = 7, \
       		textvariable= self.upper_wvl)
       	self.upper_wvl_entry.grid(row = 23, column = 1, sticky = 'NW')
        self.upper_wvl_entry.insert(0, str(default_high_wvl))
       	tk.Label(self.master, text='Upper').grid(row=24, column=1, sticky = 'NW')

       	tk.Label(self.master, text = u'Wavelength Range (\u03bcm)').grid(row=22, column=0, \
       		columnspan=2, sticky = 'NW', padx=(80,0))

       	#Next Spectrum Button 
       	self.next_button = tk.Button(self.master, text = 'Next', \
       		command = self.next_spec)
       	self.next_button.grid(row = 23, column = 13, sticky = 'NE', padx=(0,80))

        #Previous Spectrum Button
        self.back_button = tk.Button(self.master, text = 'Back', \
          command = self.prev_spec)
        self.back_button.grid(row=23, column = 12, sticky = 'NE')


    def browse_wrk_dir(self):
    	select_wrk_dir = askdirectory()
    	self.wrk_dir_entry.delete(0, 'end')
    	self.wrk_dir_entry.insert(0, select_wrk_dir)


    def browse_target_list(self):
    	select_target_list = askopenfilename()
    	self.target_list_loc_entry.delete(0, 'end')
    	self.target_list_loc_entry.insert(0, select_target_list)


    def load_list(self):
      self.ymin = np.inf
      self.ymax = -np.inf

      self.list_counter = 0

      list_load_err = False

      try:
        self.get_columns()
        self.date, self.file_no, self.obsid, self.RA, self.DEC = np.loadtxt(self.target_list_loc_entry.get(), \
          unpack=True, delimiter=',', dtype=str, usecols=self.col_tuple)

        self.file_no = self.file_no.astype(int)
      except IOError:
        tkMessageBox.showwarning(\
          'Warning', 'Could not locate specified target list.')
        list_load_err = True
      except ValueError:
        tkMessageBox.showwarning(\
          'Warning', 'Encountered problem loading list.')
        list_load_err = True


      if list_load_err==False:
        if self.overplot_on.get():
          self.overplot()
          self.flag_button.config(state='disabled')
        else:
          self.flag_list = np.zeros(len(self.date))
          self.next_spec()
          self.flag_button.config(state='normal')
          self.list_loaded=True


    def next_spec(self):
      self.list_counter+=1

      if self.list_counter==len(self.date):
        tkMessageBox.showwarning(\
          'Warning', 'Reached end of list.')
        self.list_counter-=1
      else:
        self.spec_ax.cla()
        self.spec_fig.canvas.draw()
        self.load_spec()
        self.display_info()


    def prev_spec(self):
      self.list_counter-=1

      if self.list_counter==0:
        tkMessageBox.showwarning(\
            'Warning', 'Reached start of list.')
        self.list_counter+=1
      else:
        self.spec_ax.cla()
        self.spec_fig.canvas.draw()
        self.load_spec()
        self.display_info()


    def overplot(self):
      self.clear_info()
      self.spec_ax.cla()
      self.list_counter =1
      while self.list_counter<len(self.date):
        self.load_spec()
        self.list_counter+=1
      

    def load_spec(self):
      print self.obsid[self.list_counter]

      H_spec_path = self.wrk_dir_entry.get() + '/' + self.date[self.list_counter] \
        + '/' + 'SDCH_' + self.date[self.list_counter] + '_' + '%04d'%self.file_no[self.list_counter] \
        + '.spec_a0v.fits'

      K_spec_path = self.wrk_dir_entry.get() + '/' + self.date[self.list_counter] \
        + '/' + 'SDCK_' + self.date[self.list_counter] + '_' + '%04d'%self.file_no[self.list_counter] \
        + '.spec_a0v.fits'

      load_err = False
      try: 
        H_hdu = fits.open(H_spec_path)
        K_hdu = fits.open(K_spec_path)

        H_spec = H_hdu[0].data
        K_spec = K_hdu[0].data

        H_wvl = H_hdu[1].data
        K_wvl = K_hdu[1].data

      except IOError:
        print 'Load spec error'
        load_err = True


      if load_err == False:
      
        self.current_spec = np.append(np.ravel(H_spec), np.ravel(K_spec))  
        self.current_wvl = np.append(np.ravel(H_wvl), np.ravel(K_wvl)) 

        range_look = self.current_spec[np.where((self.current_wvl>=float(self.lower_wvl_entry.get())) \
          & (self.current_wvl<=float(self.upper_wvl_entry.get())))]


        div_factor = np.nanmedian(range_look)

        self.current_spec/=np.nanmedian(range_look)
        range_look/=np.nanmedian(range_look)

        if self.overplot_on.get():
          if np.nanmin(range_look)<self.ymin:
            self.ymin = np.nanmin(range_look)

          if np.nanmax(range_look)>self.ymax:
            self.ymax = np.nanmax(range_look)

        else:
          self.ymin = np.nanmin(range_look)
          self.ymax = np.nanmax(range_look)

        
        for i in range(0,K_wvl.shape[0]):
          self.spec_ax.plot(K_wvl[i,100:1950], K_spec[i,100:1950]/div_factor)


        self.spec_ax.set_xlim(float(self.lower_wvl_entry.get()), float(self.upper_wvl_entry.get()))
        self.spec_ax.set_ylim(self.ymin, self.ymax)

        self.spec_fig.canvas.draw()

        self.check_flag()



    def display_info(self):
      self.display_obsid.configure(text=self.obsid[self.list_counter])
      self.display_obsdate.configure(text=self.date[self.list_counter])
      self.display_RA.configure(text=self.RA[self.list_counter])
      self.display_DEC.configure(text=self.DEC[self.list_counter])


    def clear_info(self):
      self.display_obsid.configure(text='')
      self.display_obsdate.configure(text='')
      self.display_RA.configure(text='')
      self.display_DEC.configure(text='')


    def flag_feature(self):
      if self.list_loaded:
        if self.flag_list[self.list_counter]==0:
          self.flag_button.config(text='Unflag')
          self.flag_display.config(text=u'\u2691')
          self.flag_list[self.list_counter]=1
        else:
          self.flag_button.config(text='Flag')
          self.flag_display.config(text='')
          self.flag_list[self.list_counter]=0
      else:
        tkMessageBox.showwarning(\
          'Warning', 'No list loaded.')


    def check_flag(self):
      if self.flag_list[self.list_counter]==1:
          self.flag_button.config(text='Unflag')
          self.flag_display.config(text=u'\u2691')
      else:
          self.flag_button.config(text='Flag')
          self.flag_display.config(text='')



    def get_columns(self):
      temp_list = np.loadtxt(self.target_list_loc_entry.get(), unpack=False, delimiter=',', dtype=str)
      col_names = temp_list[0,:]

      for i in range(0,len(col_names)):
        col = col_names[i].upper().strip()

        if col=='CIVIL':
          self.date_col = i
        elif col=='FILENUMBER':
          self.fileno_col = i
        elif col == 'OBJNAME':
          self.obsid_col = i
        elif col == 'RA':
          self.RA_col = i
        elif col == 'DEC':
          self.DEC_col = i

      self.col_tuple = (self.date_col, self.fileno_col, self.obsid_col, self.RA_col, self.DEC_col)


    def save_output(self):
      if self.list_loaded:
        save_list = np.loadtxt(self.target_list_loc_entry.get(), unpack=False, delimiter=',', dtype=str)

        save_flag_list = np.copy(self.flag_list)
        save_flag_list = save_flag_list.astype(str)
        save_flag_list[0]=self.feature_entry.get()

        save_list = np.column_stack((save_list,save_flag_list))

        save_name = self.target_list_loc_entry.get().replace('.csv', '_flagged_ouput.csv')

        np.savetxt(save_name, save_list.astype(str), delimiter=',', fmt='%s')



    def _quit(self):
    	self.master.quit()
        self.master.destroy()



if __name__ == '__main__':
  root = tk.Tk()
  root.lift()
  root.attributes('-topmost',True)
  root.after_idle(root.attributes,'-topmost',False)
  main = ViewSpec(root)
  main.grid(row=0,column=0)
  root.mainloop()