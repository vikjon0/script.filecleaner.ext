import sys
import xbmc
import xbmcaddon
import xbmcgui
import time
import sqlite3
import errno
import os
import shutil

#enable localization
getLS   = sys.modules[ "__main__" ].__language__
__cwd__ = sys.modules[ "__main__" ].__cwd__
__addonID__ = "script.filecleaner.ext"
__settings__ = xbmcaddon.Addon(__addonID__)
__title__ = "XBMC File Cleaner Extended"

addon = xbmcaddon.Addon(id = __addonID__)
addonPath = addon.getAddonInfo('path')
addonUserdata = xbmc.translatePath(addon.getAddonInfo('profile'))
addon_db = addonUserdata + 'addon.db'
    
class GUI(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.msg = kwargs['msg']
        self.first = kwargs['first']
        self.doModal()


    def onInit(self):
        self.defineControls()
        self.reload_settings()

        self.status_label.setLabel(self.msg)
        
        self.showDialog()
        
        if self.first == True:
            pass
            

        
        
        #self.setFocus(self.list)
        #self.disconnect_button.setEnabled(False)
        #self.delete_button.setEnabled(False)
        
    def defineControls(self):
        #actions
        self.action_cancel_dialog = (9, 10)
        #control ids
        self.control_heading_label_id         = 2
        self.control_list_label_id            = 3
        self.control_list_id                  = 10
        self.control_list2_id                  = 20
        self.control_save_button_id           = 11
        self.control_reload_button_id           = 13
        self.control_purge_button_id           = 14
        self.control_cancel_button_id         = 19
        self.control_status_label_id          = 100
        
        #controls
        self.heading_label      = self.getControl(self.control_heading_label_id)
        self.list_label         = self.getControl(self.control_list_label_id)
        self.list               = self.getControl(self.control_list_id)
        self.list2               = self.getControl(self.control_list2_id)
        self.save_button        = self.getControl(self.control_save_button_id)
        self.reload_button      = self.getControl(self.control_reload_button_id)
        self.purge_button     = self.getControl(self.control_purge_button_id)
        #self.disconnect_button  = self.getControl(self.control_disconnect_button_id)
        self.cancel_button      = self.getControl(self.control_cancel_button_id)
        self.status_label       = self.getControl(self.control_status_label_id)

    def showDialog(self):
        self.readLists()
        self.updateList()

        self.setFocus(self.list)
        
    def closeDialog(self):
        self.close()

    def onClick(self, controlId):
        self.msg = ""
        self.status_label.setLabel(self.msg)
        
                
        if controlId == self.control_list_id:
            position = self.list.getSelectedPosition()
            
            #get select item
            item = self.list.getSelectedItem()
            
            #self.list.removeItem(position)
            self.delete_list.append(self.keep_list[position])
            del self.keep_list[position]
           
            self.updateList()
            
        if controlId == self.control_list2_id:
            position = self.list2.getSelectedPosition()
            
            #get select item
            item = self.list2.getSelectedItem()
            
            self.keep_list.append(self.delete_list[position])
            del self.delete_list[position]
           
            self.updateList()
            

        #Save button
        elif controlId == self.control_save_button_id:
            self.save_both_lists()
            self.readLists()
            self.updateList()
            
            self.msg = getLS(300)
            self.status_label.setLabel(self.msg)
            
        elif controlId == self.control_reload_button_id:
            self.readLists()
            self.updateList()       
            
        elif controlId == self.control_purge_button_id:
            dialog = xbmcgui.Dialog()
            if dialog.yesno(getLS(303), "%s (%s)" % (getLS(304),self.holdingFolder)):
                delete_content(self.holdingFolder)             
                self.msg = getLS(302)
                self.status_label.setLabel(self.msg)
            
        #cancel dialog
        elif controlId == self.control_cancel_button_id:
            self.closeDialog()

    
    def onAction(self, action):
        if action in self.action_cancel_dialog:
            self.closeDialog()

    def onFocus(self, controlId):
        print ("testfocus")
        msg = ""
        if hasattr(self, 'status_label'):
            self.status_label.setLabel(msg)

        if controlId == self.control_purge_button_id:
            holding_size = get_size(self.holdingFolder)/1000000000
            
            self.msg = "%s (%s): %s GB" % (getLS(301), self.holdingFolder, round(holding_size,6))
            self.status_label.setLabel(self.msg)

    
    def readLists(self):
        self.delete_list = self.get_delete_list()
        self.keep_list = self.get_keep_list() 
              
    def updateList(self):
        print "updating list"
        self.list2.reset()
        self.list.reset()  
        
        if self.delete_list:
            #for idShow, description, autoDelete in delete_list:
            for idShow, description, autoDelete in self.delete_list:
                item = xbmcgui.ListItem (label=str(idShow), label2 = description)
                #item.setProperty('ssid',connection_dict['ssid'])
                self.list2.addItem(item)
         
     
        if self.keep_list:
            for idShow, description, autoDelete in self.keep_list:
                item = xbmcgui.ListItem (label=str(idShow), label2 = description)
                #item.setProperty('ssid',connection_dict['ssid'])
                self.list.addItem(item)
                
                
                
    def get_keep_list(self):
        results = []
        try:
            folder = os.listdir(xbmc.translatePath('special://database/'))
            for database in folder:
                if database.startswith('MyVideos') and database.endswith('.db'):                    
                    con = sqlite3.connect(xbmc.translatePath('special://database/' + database))
                    cur = con.cursor()
                    
                    query = "attach database '" + addon_db + "' as addon"
                    cur.execute(query)
             
                    query = "select tvshow.idShow,tvshow.c00 as showname , autoDelete from tvshow "
                    query += " left outer join addon.tvshowsettings on addon.tvshowsettings.idShow = tvshow.idShow"
                    
                    if self.tv_default == 'delete':
                        query += " where tvshow.idShow  in (select idShow from addon.tvshowsettings  where autoDelete = 0)"
                    else:
                        query += " where tvshow.idShow not in (select idShow from addon.tvshowsettings  where autoDelete = 1)"
                    
                    self.debug("Executing query on %s: %s" % (addon_db, query))
                    cur.execute(query)
                            
                    self.debug("Executing " + str(query))
                    cur.execute(query)
                    #ex = cur.fetchone()[0]
                    results = cur.fetchall()
                    return results
        
        except OSError, e:
            self.debug("Something went wrong while opening the database folder (errno: %d)" % e.errno)
            raise
        except sqlite3.OperationalError, oe:
            # The video database(s) could not be opened, or the query was invalid
            self.debug(__settings__.getLocalizedString(34002))
            msg = oe.args[0]
            self.debug(__settings__.getLocalizedString(34008) % msg)
        finally:
            cur.close()
            con.close()

    def get_delete_list(self):
        results = []
        try:
            folder = os.listdir(xbmc.translatePath('special://database/'))
            for database in folder:
                if database.startswith('MyVideos') and database.endswith('.db'):                    
                    con = sqlite3.connect(xbmc.translatePath('special://database/' + database))
                    cur = con.cursor()
                    
                    query = "attach database '" + addon_db + "' as addon"
                    cur.execute(query)
             
                    query = "select tvshow.idShow,tvshow.c00 as showname , autoDelete from tvshow "
                    query += " left outer join addon.tvshowsettings on addon.tvshowsettings.idShow = tvshow.idShow"
                    
                    if self.tv_default == 'delete':
                        query += " where tvshow.idShow not in (select idShow from addon.tvshowsettings  where autoDelete = 0)"
                    else:
                        query += " where tvshow.idShow in (select idShow from addon.tvshowsettings  where autoDelete = 1)"
                    
                    
                    self.debug("Executing query on %s: %s" % (addon_db, query))
                    cur.execute(query)
                            
                    self.debug("Executing " + str(query))
                    cur.execute(query)
                    #ex = cur.fetchone()[0]
                    results = cur.fetchall()
                    return results
        
        except OSError, e:
            self.debug("Something went wrong while opening the database folder (errno: %d)" % e.errno)
            raise
        except sqlite3.OperationalError, oe:
            # The video database(s) could not be opened, or the query was invalid
            self.debug(__settings__.getLocalizedString(34002))
            msg = oe.args[0]
            self.debug(__settings__.getLocalizedString(34008) % msg)
        finally:
            cur.close()
            con.close()
            
    def save_both_lists(self):
        for idShow, description, autoDelete in self.keep_list:
            self.save_show(idShow, description, 'keep')
        
        for idShow, description, autoDelete in self.delete_list:
            self.save_show(idShow, description, 'delete')
           
    def save_show(self,idShow,description, action):
        try:
            con = sqlite3.connect(addon_db)
            cur = con.cursor()
            
            if action == 'keep':
                autoDelete = 0
            elif action == 'delete':
                autoDelete = 1
            else:
                return
            
            # Insert if it doesn't exist
            query = "INSERT OR IGNORE INTO"
            query += " tvshowsettings"
            query += " values(%s,'%s',%s)" % (idShow, description, autoDelete)
            
            self.debug("Executing query on %s: %s" % (addon_db, query))
            cur.execute(query)
            
            
            # Update 
            query = "UPDATE OR IGNORE tvshowsettings"
            query += " SET autoDelete = %d" % autoDelete
            query += " WHERE idShow = %d" % idShow
            
            self.debug("Executing query on %s: %s" % (addon_db, query))
            cur.execute(query)
            con.commit()
        except OSError, e:
            self.debug("Something went wrong while opening the database folder (errno: %d)" % e.errno)
            raise
        except sqlite3.OperationalError, oe:
            # The video database(s) could not be opened, or the query was invalid
            self.debug(__settings__.getLocalizedString(34002))
            msg = oe.args[0]
            self.debug(__settings__.getLocalizedString(34008) % msg)
        finally:
            cur.close()
            con.close()
            
    def debug(self, message):
        """
        logs a debug message
        """
        if self.debuggingEnabled:
            xbmc.log(__title__ + " - GUI" + "::" + message)
            
    def reload_settings(self):
        """
        Retrieve new values for all settings, in order to account for any recent changes.
        """
        __settings__ = xbmcaddon.Addon(__addonID__)
        
        self.deletingEnabled = bool(__settings__.getSetting("service_enabled") == "true")
        self.delayedStart = float(__settings__.getSetting("delayed_start"))
        self.scanInterval = float(__settings__.getSetting("scan_interval"))
        
        self.notificationsEnabled = bool(__settings__.getSetting("show_notifications") == "true")
        self.debuggingEnabled = bool(xbmc.translatePath(__settings__.getSetting("enable_debug")) == "true")
        
        self.enableExpiration = bool(__settings__.getSetting("enable_expire") == "true")
        self.expireAfter = float(__settings__.getSetting("expire_after"))
        
        self.deleteOnlyLowRated = bool(__settings__.getSetting("delete_low_rating") == "true")
        self.minimumRating = float(__settings__.getSetting("low_rating_figure"))
        self.ignoreNoRating = bool(__settings__.getSetting("ignore_no_rating") == "true")
        
        self.deleteUponLowDiskSpace = bool(__settings__.getSetting("delete_on_low_disk") == "true")
        self.diskSpaceThreshold = float(__settings__.getSetting("low_disk_percentage"))
        self.diskSpacePath = xbmc.translatePath(__settings__.getSetting("low_disk_path"))
        
        self.cleanLibrary = bool(__settings__.getSetting("clean_library") == "true")
        self.deleteMovies = bool(__settings__.getSetting("delete_movies") == "true")
        self.deleteTVShows = bool(__settings__.getSetting("delete_tvshows") == "true")
        
        self.holdingEnabled = bool(__settings__.getSetting("enable_holding") == "true")
        self.holdingFolder = xbmc.translatePath(__settings__.getSetting("holding_folder"))
        self.createSubdirectories = bool(xbmc.translatePath(__settings__.getSetting("create_series_season_dirs")) == "true")
        self.updatePaths = bool(xbmc.translatePath(__settings__.getSetting("update_path_reference")) == "true")
        
        self.removeFromAutoExec = bool(xbmc.translatePath(__settings__.getSetting("remove_from_autoexec")) != "false")
    
        #--vikjon0 mod---------
        self.tv_default = __settings__.getSetting('tv_default')


def get_size(start_path = '.'):
    total_size = float(0)
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
              
    return total_size


def delete_content(start_path):
    for the_file in os.listdir(start_path):
        file_path = os.path.join(start_path, the_file)
        print file_path
        if os.path.islink(file_path):
            os.unlink(file_path)
        else:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        
            
                
