#ifndef __ARS_API_H__
#define __ARS_API_H__

extern int onStart(void);
extern int onStop(void);

extern int onSave(const char *);
extern int onResume(const char *);
extern int onClose(const char *);

extern int onTrigger(void *);

#endif