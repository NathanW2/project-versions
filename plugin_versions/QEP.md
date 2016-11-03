# QGIS Enhancement: Project backup and versioning

**Date** 2016/11/02
**Author** Nathan Woodrow @NathanW2
**Contact** woodrow.nathan@gmail.com
**maintainer** @NathanW2
**Version** QGIS 3.0

# Summary

Have you ever used Office 356 or Google Docs and found the revision history function handy? Well why not have the same thing in QGIS. Think how powerful it would be to be able to restore older versions of the current open project, and never worry about busting your project again.

This QEP outlines the ability to be able to store project revisions/backups with the ability to rollback to older versions if needed.  Being able to rollback to older copies of a document is a handy feature with a lot of web tools today and brining this into QGIS would increase the user friendliness of the application. Having auto revision also allows the user to experiment without worry.

## Current solution

Currenlty each time the project is saved a `.qgs~` file is created.  This looks fine, however, this only gives you single point of rollback and requires users to rename the file manually in order to restore the backup.  There have been cases, altough rare, of a project file getting corrupted, while this is a rare case having a built in system would avoid bad cases like that. 

If you need to keep revisions of your project files you are currently required to take file backups and we all know where that leads. `project.copy.qgs`, `project.copy2.qgs`, project.IDontKnowWhatVersion.qgs`. You get the point.   There is no need for the user to manage the project file on disk. Of course there is nothing stoping the user doing that if they still wish.

## Proposed Solution

The proposed solution is to store a copy of the project XML blob compressed in a single sqlite database with a timestamp, filename, project name, and some other metadata.  This allows QGIS to manage all backups and file revisions itself with a nice UI in order to rollback to older/newer versions.

A example of the table:

```
      CREATE TABLE IF NOT EXISTS projects (
          name TEXT,
          "save_date" datetime,
          filepath TEXT,
          xml BLOB,
          tag TEXT);
```

Each time the user saves a compressed copy of the XML blob is saved in the database along with the name, filename, date stamp, etc.  The user also has the ability to save a tag against that save point.  Tags are simply named points in time.

When a point in time is selected the XML is loaded from the database, writtem to disk, and reloaded in the session.

The feature will also have the ability to define other storage types using a simple API. These could include MS SQL, Postgres, web service.  This can allow for enterprise style setups where the data might be stored of local PCs and in a database. Storage writes can be done in a thread to avoid locking the UI.

## Performance Implications

Storage calls must be threaded in order to not block UI. 

## Storage Implications

Storing a copy of the XML on each save could lead to a lot of data being kept. A couple of methods to help combat this:

- The XML is compresed to reduce the size.
- Any versions without a tag and older then a set time can be removed (config option maybe)
- Using a different storage option e.g MS SQL - This would be a config option with sqlite being the default.

## Further Considerations

One option I did consider was using a git style, or even git itself, to handle the revision and storage. This might still be a option and will
some investigation. I feel the git method adds lots of complication which isn't really needed and feels like a bit of a hack.  The git option might be better if the history was stored along side the project however, I feel that only makes sense if we have a custom project file format which includes other files aka KMZ files.

I have implemented this basic project versioning idea in a plugin which can be found here: ()

With the basic API it would be quite easy to test different storage methods to check the workflow.


## Further Improvements

## Backwards Compatibility

New feautre will no effect on older installs.

## Issue Tracking ID(s)

## Votes

(required)
