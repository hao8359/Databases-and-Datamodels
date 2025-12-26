package com.github.cm2027.lab3datalake.hacks;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.LocatedFileStatus;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.fs.RemoteIterator;

import com.github.cm2027.lab3datalake.Session;

public class TrinoHistoryFix {

    /**
     * Ensure the .hoodie/timeline/history folder is deleted if empty.
     * Safe to call multiple times (idempotent).
     */
    public static void ensureEmptyHistoryDeleted(String path) throws Exception {
        Configuration conf = new Configuration();
        conf.set("fs.defaultFS", Session.HDFS_BASE_URI);
        FileSystem fs = FileSystem.get(conf);

        Path historyPath = new Path(Session.HDFS_BASE_URI + path + "/.hoodie/timeline/history");
        if (fs.exists(historyPath)) {
            // Check if folder is empty
            RemoteIterator<LocatedFileStatus> files = fs.listFiles(historyPath, false);
            if (!files.hasNext()) {
                fs.delete(historyPath, true); // recursive delete
                System.out.println("Deleted empty history folder");
            } else {
                System.out.println("History folder exists and is not empty, leaving it intact");
            }
        } else {
            System.out.println("History folder does not exist");
        }
    }

}
