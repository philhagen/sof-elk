#!/usr/bin/python
#Frequency Counter Object - Mark Baggett @markbaggett
#This object is used to count the frequency of characters appearance in text.
#See https://isc.sans.edu/diary/Detecting+Random+-+Finding+Algorithmically+chosen+DNS+names+%28DGA%29/19893
import pickle

class CharCount(dict):
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = 0
        return value

class FreqCounter(dict):
  """This object is used for counting the frequency of characters that follow other characters. It supports saving the data structure and loading it from disk.  The printtable() method is used to generate python source code to lookup the characters in frequency order.  Other key methods include tallyfile(), tallydict(), printraw(), save(), load(), probability() and resetcounts().  Check the help on each of them for more details.

Here is an example of how this object might be used.

>>> from freq import *                  -  Import the Module
>>> c=FreqCounter()                     -  Create an object to count characters
>>> c.tally_str(open("mobydick.txt").read())  - Count the character pairs in moby dick
>>> c.probability("er")              -  In moby dick what is the probability r follows e
18.758395940096523
>>> c.probability("qu")              -  What is probability u follows q
99.93618379068283
>>> c.lookup("s")                       -  Show me the characters, in order of probability, that would follow an s
'teoh,isaup.clmwkn-yqfbdgrj'
>>> c["q"]["u"]                         -  How many times did u follow q in Moby Dick
1566
>>> b=FreqCounter()                     -  Create another object
>>> b.load("all_plus_cr.freq")          -  load a previously created frequency count
>>> b.printtable()                      -  print a python function to do the same thing as .lookup() above
def lookupfreq(index):                  -  This is sample output of printtable() is truncated.  You get the idea.
  return {
    "[": "23t591a4068ojicprlm*n.ebgf]w[hys7d"/%!#kv+,u-<:^>($x@?z_{\`&=q;|)~}",
    "$": "123n456798)ascp0tdivblrhfm<(u$e_@o,kwy-"qxg!/`\]%j;z:^#*=+|?.{>[&}~",
    "<": "fic/sbtmpekrvwanjd0h<lguxo,&1[->4="7?q%52$36!@.8;\9#:yz+|*(_)^]`{}~",
    "#": "#0lsi1dgcf<em2_t73a)j6$bu"p9(hr`.n!4,{58;q:v@*xo[kzw\%]-?y|/=+^&>}~",
    "/": "1wmadcrvu/psfiteo2lgb>jzn0435h769x.8*k~q\")y_@+^%<[-?,`$:;]!{|#(=&}",
    "^": "[6^c5]v\%21"_mfxeq3atso07=#w(/.bd-hirnlu@*gpy,4;<$9!>?zkj+&:8`|{)~}",
    "+": "0+-41"cxrfpdaesio=3wg/bl2m]t)%vjqunhy7`z6k(,8;.?9#\5>$&:*^[!<@|_{}~",
    "\": "xn"s\ca$emdt%w.jr(vp)<@_0fb-z/ou1i>hl+{|q2?=3g*:ky&9^;,]578![`#64~}",
    "|": "|{srbuc:.veydztfnxmwgpialq9$2+o-h0),1k4j/3@=<58"[_6~7]>;#%\(?`!&*^}",
    "{": "{12n"eoclpfstv3rmk$bxhdgwzi|ju874`_65\90?@a</[y]-(,;=^}:%*&+)#>q.!~",
    " ": "tahswiombcf dplnrgeyu
kvj"q-(1.`xz2*345&_6907{[$8?,!@#;~)=:",
  }[index]
>>> b.probability("qu")              - In all_plus_cr what is the probability that u follows q
97.53780054759638
>>> b.lookup("q")                       - print in order of probability the characters that will follow a q
'ua.il,qsecrkbd|yz9owvmpgt-hn0f)?j_6x"124/:5+;{37=@8%<\\(*![]$^& >#`~}'
>>> b.promote("q","l",2)                - promote the probability l will follow q by 2 characters.
>>> b.lookup("q")                       - Now is l is more likely to follow q
'ual.i,qsecrkbd|yz9owvmpgt-hn0f)?j_6x"124/:5+;{37=@8%<\\(*![]$^& >#`~}'
"""

  def __init__(self,*args,**kargs):
      self.ignorechars = """\n\t\r~@#%^&*"'/\-+<>{}|$!:()[];?,="""
      self. ignorecase = True
      super(FreqCounter, self).__init__(*args,**kargs)

  def __getitem__(self, item):
      try:
          return dict.__getitem__(self, item)
      except KeyError:
          value = self[item] = CharCount()
      return value

  def tally_str(self,line,weight=1):
      """tally_str() accepts two parameters.  A string and optionally you can specify a weight."""
      wordcount=0
      if self.ignorecase:
          line=line.lower()
      for char in range(len(line)-1):
          if line[char] in self.ignorechars or line[char+1] in self.ignorechars:
              continue
          if line[char+1] in self[line[char]]:
              self[line[char]][line[char+1]]=self[line[char]][line[char+1]]+(1*weight)
          else:
              self[line[char]][line[char+1]]=weight
      return wordcount

  def probability(self,string,max_prob=40):
      """This function tells you how probable the letter combination provided is giving the character frequencies. Ex .probability("test") returns ~%35 """
      probs=[]
      for pos,ch in enumerate(string[:-1]):
          if not ch in self.ignorechars and not string[pos+1] in self.ignorechars:
              probs.append( self._probability(ch,string[pos+1],max_prob) )
      if len(probs)==0:
          return 0
      return sum(probs) / len(probs)

  def printtable(self):
      """ Prints the frequency tables as a python function that can be used to lookup the characters that follow a character.  You can plug the resulting script into a python program to lookup the most frequent character to follow another character.  For example you can call "lookupfreq("q")" and it will return a string containing all the characters in frequency order such as "ustrnalq1f"   where "u" is the most frequenct character to follow "q" and "f" is the least frequent.
    """
      print "def lookupfreq(index):"
      print "    #Although it may not aways be the past data collected.  The current setting for this file are:"
      print "    #The following characters are currently ignored: %s :" % (self.ignorechars.encode("string_escape"))
      if self.ignorecase:
          print "    #It currently ignores case for all calculations."
      else:
          print "    #It is currently case sensitive for all calculations."
      print "    return {"
      for keys in sorted(self.keys(),reverse=True, key=self.get):
          print "    \""+str(keys)+"\":",
          letters=""
          for subkeys in sorted(self[keys].keys(),reverse=True, key=self[keys].get):
              letters=letters+subkeys
          print '"'+letters.encode("string_escape")+'",'
          print "    }[index]"

  def lookup(self,letter):
      """ Returns a string of characters in frequency order. """
      if self.ignorecase: letter = letter.lower()
      return "".join(sorted(self[letter].keys(),reverse=True, key=self[letter].get))

  def _probability(self,top,sub,max_prob=40):
      """This internal only function will print the probability that a character will follow another.
      Example: counter._probability("q","u") - Will tell you the chance that U will follow Q based on the data in the character frequency counter object.  For example,  If you have a Q there is approximately a 30% chance that the next character is a U."""
      if self.ignorecase:
          top = top.lower()
          sub = sub.lower()
      if not self.has_key(top):
          return 0
      all_letter_count = sum(self[top].values())
      char2_count = 0
      if self[top].has_key(sub):
          char2_count = self[top][sub]
      probab = float(char2_count)/float(all_letter_count)*100
      if probab > max_prob:
          probab = max_prob
      return probab

  def printraw(self):
      """Prints the raw python data structure containing the frequency table."""
      print self

  def save(self,filename):
      """Saves the raw python data structure from the file specified.  Save and Load are used to write the data structure to disk so you can come back to it later or exchange them with other developers.
Example:
counter.save("/home/user/savedfreqcounter.txt") - save the data structure from disk.
"""
      try:
          file_handle =  open(filename, 'wb')
          data =  [ self.items(), self.ignorechars, self.ignorecase ]
          pickle.dump(data, file_handle)
          file_handle.flush()
          file_handle.close()
      except Exception as e:
          print "Unable to write freq file :"+str(e)
          

  def load(self,filename):
      """Loads the raw python data structure from the file specified. Load is using the raw data structures. Save and Load are used to write the data structure to disk so you can come back to it later or exchange them with other developers.  This is not the same as tallyfile.  Tallyfile analyzes a files character frequencies.
Example:
counter.load("/home/user/savedfreqcounter.txt") - Loads the data structure from disk.
"""
      try:
          file_handle = open(filename, 'rb')
          stored_values = pickle.load(file_handle)
          self.update(stored_values[0])
          self.ignorechars = stored_values[1]
          self.ignorecase = stored_values[2]
      except Exception as e:
          print "Unable to load freq file :"+str(e)


  def promote(self,top,sub,weight):
      """Promotes sub up weight positions inside of tops array.
Example:
counter.promote("c","a",5) - a will move up 5 places in c's table
"""
      chartable=self[top]
      currentoffset=self.lookup(top).index(sub)
      if currentoffset<weight:
          currentoffset=weight
      movebeforeletter=sorted(chartable.keys(),reverse=True, key=chartable.get)[currentoffset-weight]
      addthisamount=self[top][movebeforeletter]-self[top][sub]+1
      self[top][sub]=self[top][sub]+addthisamount
      return

  def resetcounts(self):
      """Reset the counts for all of the character frequencies to 1 giving every character an equal probability of following other characters."""
      for keys in self.keys():
          for subkeys in self[keys].keys():
              self[keys][subkeys]=1

def main():
    import argparse
    import os
    import sys
    import shutil

    parser=argparse.ArgumentParser()
    parser.add_argument('-m','--measure',required=False,help='Measure likelihood of a given string',dest='measure')
    parser.add_argument('-b','--bulk_measure',required=False,help='Measure each line in a file',dest='bulk_measure')
    parser.add_argument('-n','--normal',required=False,help='Update the table based on the following normal string',dest='normal')
    parser.add_argument('-f','--normalfile',required=False,help='Update the table based on the contents of the normal file',dest='normalfile')
    parser.add_argument('-o','--odd',required=False,help='Update the table based on the contents of the odd string. It is not a good idea to use this on random data',dest='odd')
    parser.add_argument('-p','--print',action='store_true',required=False,help='Print a table of the most likely letters in order',dest='printtable')
    parser.add_argument('-c','--create',action='store_true',required=False,help='Create a new empty frequency table',dest='create')
    parser.add_argument('-v','--verbose',action='store_true',required=False,help='Print verbose output',dest='verbose')
    parser.add_argument('-t','--toggle_case_sensitivity',action='store_true',required=False,help='Ignore case in all future frequecy tabulations',dest='toggle_case')
    parser.add_argument('-M','--max_prob',required=False,default=40,type=int,help='Defines the maximum probability of any character combo. (Prevents "qu" from overpowering stats) Default 40',dest='max_prob')
    parser.add_argument('-P','--promote',required=False,nargs=2,help='This takes 2 characters as arguments.  Given the 2 characters, promote the likelihood of the 2nd in the first by <weight> places',dest='promotelist')
    parser.add_argument('-w','--weight',type=int,default = 1, required=False,help='Affects weight of promote, update and update file (default is 1)',dest='weight')
    parser.add_argument('-e','--exclude',default = "", required=False,help='Change the list of characters to ignore from the tabulations.',dest='exclude')
    parser.add_argument('freqtable',help='File storing character frequencies.')

    args=parser.parse_args()

    fc = FreqCounter()

    if args.create and os.path.exists(args.freqtable):
        print "Frequency table already exists. "+args.freqtable
        return 1

    if not args.create:
        if not os.path.exists(args.freqtable):
           print "Frequency Character file not found. - %s " % (args.freqtable)
           return
        shutil.copyfile(args.freqtable, args.freqtable+".bak")
        fc.load(args.freqtable)

    if args.verbose:
        print "Ignored characters specified in frequency table are:"+str(fc.ignorechars)
        print "Case sensitivity is set to "+str(not fc.ignorecase)

    if args.printtable: fc.printtable()
    if args.normal: fc.tally_str(args.normal, args.weight)
    if args.odd: fc.tally_str(args.odd, (args.weight * -1))
    if args.exclude:
        fc.ignorechars = args.exclude
        print "Ignored characters changed to "+str(fc.ignorechars)
    if args.toggle_case:  
        fc.ignorecase = not fc.ignorecase
        print "Case sensitivity is now set to "+str(not fc.ignorecase)
    if args.normalfile:
        try:
            filecontent = open(args.normalfile).read()
        except Exception as e:
            print "Unable to open normal file. " + str(e)
            return 1
        fc.tally_str(filecontent)
    if args.measure: print fc.probability(args.measure, args.max_prob)
    if args.bulk_measure:
        try:
            filecontent = open(args.bulk_measure).readlines()
        except Exception as e:
            print "Unable to open bulk measure file. " + str(e)
            return 1
        for eachentry in filecontent:
            eachentry=eachentry.strip()
            print "[+]",eachentry, fc.probability(eachentry, args.max_prob)
    if args.promotelist: fc.promote(args.promotelist[0], args.promotelist[1], args.weight)
    fc.save(args.freqtable)

if __name__ == "__main__":
    main()


