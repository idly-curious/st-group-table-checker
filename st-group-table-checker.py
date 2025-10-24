import streamlit as st
import matplotlib.pyplot as plt
import math
import time
import numpy as np  # numpy arrays seem fastest for table ops
                    # particularly transpose

#import pandas as pd # only used for reading CSV file

# shell command:
# streamlit run st-group-table-checker.py

# using np array for group table makes things much faster
# than the original code using lists
#
# table.max() gives max
# table.min() gives min
# so closure is easy
#
# comparing arrays: (a==b).all()
# instead of list comprehension
# [a[b[j]] for j in x]
# use a[b[x]] with arrays
#
# column of array: a[:,j] but row of transpose is faster




# new feature: test mode, allows testing of algorithm on much bigger 
# tables
#
# test mode menu:
# * simple diagnostics: tables which generate all types of output
#   (currently need more examples which fail associativity with
#   triple_type 'roadmap left' or 'roadmap right'). Probably just
#   some small modified group tables where for some involution
#   r, the a and ar rows intersect the b and rb columns have
#   ab's and arb's swapped
#
# * timing results on big tables
#
#

#####################################################################
# streamlit code to demonstrate how to test whether a (n x n) table #
# defines a group, checking only n^2 ish triples for associativity  #
#####################################################################
class group_table_checker(object):

    ##################################################################
    #  versions of list and dict which allow setattr                 #
    ##################################################################
    class List(list): 
        def __init__(self, initial_data=None):
            if initial_data is None:
                initial_data = []
            super().__init__(initial_data)
    #---------------------------------------------------------------#
    class Dict(dict):
        def __init__(self, initial_data=None):
            if initial_data is None:
                initial_data = []
            super().__init__(initial_data)

    ##################################################################
    # attribute to make appending to roadblock work with cell colors #
    ##################################################################
    def roadmap_add(self,equation):
        self.roadmap.append(equation)
        if not self.test_mode:
            i=equation['x']
            j=equation['y']
            self.cell_colors[i][j]=self.road_color
        
    ##################################################################
    # attributes to make a FIFO queue out of a list                  #
    ##################################################################
    def Queue_pop(self):
        item=self.Queue[self.Queue.ptr]
        if not self.test_mode:
            i=item['x']
            j=item['s']
            self.cell_colors[i][j]=self.crossed
        self.Queue.ptr=self.Queue.ptr+1
        return item
    #---------------------------------------------------------------#
    def Queue_size(self):
        return len(self.Queue)-self.Queue.ptr
    
    ##################################################################
    # attributes to make H and S affect Queue appropriately          #
    ##################################################################
    def H_add(self,x):
        self.H[x] = True
        
        for s in self.S:
            self.Queue.append({'x':x,'s':s})

        if not self.suppress_output:
            self.row_colors[x]=self.H_color
            for j in range(0,self.n):
                self.cell_colors[x][j]=self.H_color
            for s in self.S:
                self.cell_colors[x][s]=self.Q_color
            self.H_string=self.H_string[:-3]+f",{self.element[x]}"+r"\}$"
            
    #---------------------------------------------------------------#
    def S_add(self,s):
        self.S.append(s)
        for x in self.H:
            self.Queue.append({'x':x,'s':s})

        if not self.suppress_output:
            self.col_colors[s]=self.S_color
            for i in range(0,self.n):
                self.cell_colors[i][s]=self.S_color
            for x in self.H:
                self.cell_colors[x][s]=self.Q_color
        if len(self.S)>1:
            self.S_string=self.S_string[:-3]+f",{self.element[s]}"+r"\}$"
        else:
            self.S_string=self.S_string[:-3]+f"{self.element[s]}"+r"\}$"

    ##################################################################
    # Initialize everything we need for testing the table.           #
    #                                                                #
    # The object, once initialized, should be stored in              #
    # st.session_state so we can resume computation after            #
    # a button press or other interaction                            #
    ##################################################################
    def __init__(self,element,table, test_mode=False):
        self.test_mode    = test_mode
        self.element      = element
        self.table        = table
        self.n            = len(element)
        self.index        = {}

        # we color the table to indicate progress
        if not test_mode:
            self.cell_colors  = []
            self.col_colors   = []
            self.row_colors   = []
            
            self.plain        = "white"     # typical table entry
        
            self.H_color      = "yellow"    # row index is an element of H
        
            self.S_color      = "pink"      # column index is an element of S
        
            self.Q_color      = "orange"    # row index in H, col index in S
            # unprocessed queue item
                                        
            self.road_color   = "#e3592e"   # row index in H, col index in S
            # processed cell which produced
            # a roadmap equation
                                        
            self.crossed      = "#d6a240"   # row index in H, col index in S
            # processed cell which did not
            # produce roadmap equation

        # check that the table is the right shape
        if not table.shape==(self.n,self.n):
            raise ValueError(f"{self.n} elements given but table is not {self.n} by {self.n}")

        # check that the list of elements consists of distinct entries
        # making a dictionary in the process that maps from elements to
        # indices
        for a in element:
            i=len(self.index)
            if a in self.index:
                raise ValueError(f"element {a} occurs twice")
            self.index[a]=i

        if element==list(range(self.n)):
            self.op = self.table 
        else:
            # store the group table in terms of indices of elements
            self.op = np.zeros((self.n,self.n),dtype=int)
            
            for i in range(self.n):
                for j in range(self.n):
                    x=self.table[i][j]
                    if x in self.index:
                        k=self.index[x]
                    else:
                        k=-1 # if the set is not closed
                             # there will be -1's in the table
                    self.op[i][j] = k
        self.opT    = self.op.T
        self.tableT = self.table.T
        
        if not test_mode:
            # initialize the table to have white background
            for a in element:
                self.row_colors.append(self.plain)
                self.col_colors.append(self.plain)
                this_row_colors=[]
                for b in element:
                    this_row_colors.append(self.plain)
                self.cell_colors.append(this_row_colors)
                
        self.roadmap = self.List([]) # list of equations. keys 'x', 'y', and 'z'
        setattr(self.roadmap,"add",self.roadmap_add)
        self.roadmap_string="roadmap equations:\n\n"
        
        self.Queue   = self.List([]) # list of items. keys 'x' and 's'
        
        setattr(self.Queue,"ptr",0)                # hack to make
        setattr(self.Queue,"pop",self.Queue_pop)   # it FIFO although
        setattr(self.Queue,"size",self.Queue_size) # that's not required
        
        self.H        = self.Dict({})

        #set H.add to H_add
        setattr(self.H,"add",self.H_add) # when we add x to H
                                         # all x,S pairs go on Queue
                                               
        self.S        = self.List([])
        self.S_string = r"$S=\{\}$"

        # set S.add to S_add
        setattr(self.S,"add",self.S_add) # when we add s to S
                                         # all H,s pairs go on Queue
                                         
        self.untried=list(range(self.n-1,-1,-1))
        # pop this when we need to try adding to S
        # we try the elements in order

        # need variable names which don't
        # conflict with group element names

        self.a_name='a'
        self.b_name='b'
        self.c_name='c'
        names=list("astuxAUbcdefghijklmnopqrvwBCDIJKLMNOPQR")
        i=0
        while (i<len(names)) and ((names[i] in element) or (chr(ord(names[i])+1) in element) or (chr(ord(names[i])+2) in element)):
            i=i+1
        if (i<len(names)):
            self.a_name=names[i]
            self.b_name=chr(ord(names[i])+1)
            self.c_name=chr(ord(names[i])+2)
            
        self.pause_between_pages = False
        self.suppress_output     = True
        self.number_of_triples   = 0
        self.roadmap_step        = 0
        self.introduced          = False
        
    ##################################################################
    # End of __init__                                                #
    ##################################################################

    ##################################################################
    # Subroutines                                                    #
    ##################################################################


    #----------------------------------------------------------------#  
    # Wait for reader to click "Proceed"
    def pause(self):
        if self.pause_between_pages:
            done=st.button("Proceed",type="primary")
            st.stop()
        else:
            st.write("----------")
            
    #----------------------------------------------------------------#  
    # Print our current status
    def print_status(self):
        fig, ax = plt.subplots()
        ax.axis('off')  # Hide axes
        ax.set_aspect('equal')
        table = ax.table(cellText=self.table,
                         cellColours=self.cell_colors,
                         cellLoc='center',
                         loc='center',
                         rowLabels=self.element,
                         rowColours=self.row_colors,
                         rowLoc='center',
                         colLabels=self.element,
                         colColours=self.col_colors,
                         colLoc='center',
                         )
        #table.auto_set_font_size(False)
        #table.set_fontsize(20)
        
        table._autoColumns=[]
        #set cell height and width.  
        for (row, col), cell in table.get_celld().items():
            if row > 0:
                cell.set_height(1/(self.n+.5))
            else:
                cell.set_height(1/(2*self.n+1))
            if col > -1:
                cell.set_width(1/(self.n+.5))
            else:
                cell.set_width(1/(2*self.n+1))

        col1,col2,col3=st.columns(3)
        col1.pyplot(fig)

        col2.write("*Group properties:*")
        if hasattr(self,"closed"):
            col2.write("Closure: verified.")
        else:
            col2.write("Closure: checking now.")
        
        if hasattr(self,"identity"):
            col2.write("Identity element is $"+(self.element[self.identity])+"$.")
        elif hasattr(self,"closed"):
            col2.write("Identity: checking now.")            
        else:
            col2.write("Identity:")            
            
        if hasattr(self,"inverse"):
            col2.write("Inverses: verified.")
        elif hasattr(self,"identity"):
            col2.write("Inverses: checking now.")
        else:
            col2.write("Inverses: ")

        if hasattr(self,"inverse"):
            if len(self.H) < self.n:
                col2.write("Associativity: computing $S$.")
            else:
                col2.write("Associativity: checking now.")
        else:
            col2.write("Associativity: ")
                
        if hasattr(self,"inverse"):
            col3.write("*Summary:*")
            col3.write(self.S_string)
            if len(self.H) < self.n:
                col3.write(self.H_string)
            if len(self.roadmap) > 0:
                col3.write("R"+self.roadmap_string[1:])
            
        plt.close(fig)
    #----------------------------------------------------------------#  
    # Just explain that the user should read everything before 
    # clicking
    
    def intro(self):

        standard = "Detailed explanations, one section at a time"
        all      = "Detailed explanations, all at once"
        minimal  = "Minimal output"
        if ('output_set' in st.session_state) and st.session_state.output_set:
            del st.session_state.output_set
            option=st.session_state.output_option
            del st.session_state.output_option
            self.introduced=True        
    
            if option==standard:
                self.pause_between_pages = True
                self.suppress_output     = False
                
            elif option==all:
                self.pause_between_pages = False
                self.suppress_output     = False
                
            else: #option==Minimal:
                self.pause_between_pages = False
                self.suppress_output     = True
        else:
            st.write("""
            # Output options

            The purpose of this program is to illustrate
            a method for testing whether a table defines a group.
            
            If this is your first time using this, or the method
            is unfamiliar to you, then you should probably
            click the one of the 'detailed explanations' options.

            On the other hand, if you are familiar with the
            algorithm, and understand the relationship between
            the generating set $S$, the *roadmap equations*,
            and the triples which need to be checked, then the
            minimal output might be right for you.  If the
            table defines a group, it will provide everything
            required for a proof.
            """)
            
            output_option=st.radio("Please choose an output option",
                                  [standard,
                                   all,
                                   minimal],
                                  key="output_option")
            st.button("Proceed", key="output_set",type="primary")
            st.stop()
        

    
    #----------------------------------------------------------------#  
    # For all elements a and b, is the a,b entry
    # in the table always an element?
    
    def test_closure(self):
        if not self.suppress_output:
            self.print_status()
            st.write("""
            # Closure
            
            Testing whether the set is closed under the operation.
            This means making sure that every entry in the table
            is actually an element of the set.
            
            """)
        if (self.op.max() >= self.n) or (self.op.min() < 0):
            I,J=np.where(np.logical_or((self.op>=self.n),(self.op<0)))
            i=I[0]
            j=J[0]
            a=self.element[i]
            b=self.element[j]
            c=self.table[i][j]
            self.failed_product = [a,b,c]
            if not self.test_mode:
                st.write(f"The element :red[${c}={a}*{b}$] is not in the set,")
                st.write("so this is not a group table.")
            return False
        self.closed=True
        if not self.suppress_output:
            st.write("It checks out! The set is closed under the operation")
        return True
    
    #----------------------------------------------------------------#    
    # is there a two-sided identity?
    # note that if there is, then there
    # cannot be a separate one-sided identity

    def test_identity(self):
        text="""
        # Identity
        
        Testing whether there is an identity element.

        The row indexed by the identity element should look
        exactly like the list of elements.
        
        """
        # first find identity row of table
        i = 0
        while (i<self.n) and not (self.table[i] == self.element).all():
            i = i+1

        if(i == self.n):
            if not self.suppress_output:
                self.print_status()
                st.write(text)
                st.write(":red[There is no such row, so there is no identity].")
                st.write("This is not a group table.")
            else:
                if not self.test_mode:
                    st.write(":red[There is no identity].")
            return False

        # we have a left identity
        identity = i
        if not self.suppress_output:
            self.row_colors[i]="yellow"
            self.col_colors[i]="yellow"
            for j in range(0,self.n):
                self.cell_colors[i][j]="yellow"
                if self.table[i][j]==self.table[j][i]:
                    self.cell_colors[j][i]="yellow"
                else:
                    self.cell_colors[j][i]="red"
                    
            self.print_status()

            self.row_colors[i]=self.plain
            self.col_colors[i]=self.plain
            for j in range(0,self.n):
                self.cell_colors[i][j]=self.plain
                if self.table[i][j]==self.table[j][i]:
                    self.cell_colors[j][i]=self.plain
                else:
                    self.cell_colors[j][i]=self.plain

            st.write(text)
        
            st.write(f"""
            We found a row that looks right!
            ${self.element[identity]}$ is a left identity.

            We have highlighted the ${self.element[identity]}$ row and
            the ${self.element[identity]}$ column.  Now we check
            whether it's also a right identity.
            """)
        

        # check if it's also a right identity
        if not (self.tableT[identity] == self.element).all():
            J=np.where(self.tableT[identity]!=self.element)
            j=J[0][0]
            a=self.element[j]
            b=self.table[j,identity]
            if not self.suppress_output:                
                st.write(f"It is not! We have :red[${a}*{self.element[identity]}={b}$].")
                st.write("This is not a group table.")
            else:
                if not self.test_mode:
                    st.write(":red[There is no identity].")                
            return False
            
        if not self.suppress_output:                
            st.write("""
            It is!
            
            """)
        self.identity = identity

        return True

    #----------------------------------------------------------------#    
    # Are there inverses ?

    def test_inverses(self):
        inverse = {}
        identity=self.identity
        a_name=self.a_name
        b_name=self.b_name
        c_name=self.c_name
        
        if not self.suppress_output:                
            for i in range(0,self.n):
                for j in range(0,self.n):
                    if(self.table[i][j]==self.element[identity]):
                        self.cell_colors[i][j]="yellow"
                        
            self.print_status()

            # make table plain again
            for i in range(0,self.n):
                for j in range(0,self.n):
                    if(self.table[i][j]==self.element[identity]):
                        self.cell_colors[i][j]=self.plain

        
            st.write(f"""
            # Inverses
            
            Testing whether all elements have two-sided inverses.
            
            For every element ${a_name}$, we seek an element ${b_name}$ such
            that ${a_name}*{b_name}={b_name}*{a_name}={self.element[identity]}$.
            
            To make it easier to check, we have highlighted
            the identity element ${self.element[identity]}$
            wherever it occurs in the table.  For there to
            be inverses, we must have a highlighted entry in every
            row and column, located symmetrically about the diagonal.
            (Technically there must be a *subset* of the
            highlighted entries with this property.)
            """)
            
        I,J=np.where(np.logical_and(self.op==identity,self.opT==identity))
        for i in range(self.n):
            if not i in I:
                a=self.element[i]
                self.failed_inverse=a
                if not self.test_mode:
                    st.write(f"""
                    :red[The element ${a}$ has no inverse].
                    This is not a group table.
                    
                    """)
                return False
                
            elif not i in inverse:
                j=J[np.where(I==i)[0]][0]
                inverse[i]=j
                inverse[j]=i
            
        if not self.suppress_output:
            st.write("All elements have inverses!")
        self.inverse=inverse
        return True


    #----------------------------------------------------------------#
    # check whether a triple satisfies associativity
    #
    # the optional arguments ab and bc are for
    # cases in which many triples with either the same
    # first two elements or same last two elements are to be tested.
    # in such cases we require only three table lookups per triple
    # instead of four
    
    def check_triple(self,a,b,c,ab=False,bc=False):
        self.number_of_triples=self.number_of_triples+1
        op=self.op
        if ab==False:
            ab   = op[a][b]
        if bc==False:
            bc   = op[b][c]
        a_bc = op[a][bc]
        ab_c = op[ab][c]

        if a_bc == ab_c:
            if not self.test_mode:
                allgood=r"${\ \ \ \ "+f"({self.element[a]}*{self.element[b]})*{self.element[c]}={self.element[ab]}*{self.element[c]}={self.element[ab_c]}={self.element[a]}*{self.element[bc]}={self.element[a]}*({self.element[b]}*{self.element[c]})"+r"\ \ \ \ \checkmark"+r"}$"
                st.write(f"{self.number_of_triples}. :green[{allgood}]")
            return True
        else:
            self.failed_triple=[self.element[a],self.element[b],self.element[c]]
            if not self.test_mode:
                violation=r"${\ \ \ \ "+f"({self.element[a]}*{self.element[b]})*{self.element[c]}={self.element[ab]}*{self.element[c]}={self.element[ab_c]}"+r"\neq "+f"{self.element[a_bc]}={self.element[a]}*{self.element[bc]}={self.element[a]}*({self.element[b]}*{self.element[c]})"+r"}$"
                st.write(f"{self.number_of_triples}. :red[{violation}]")
                st.write("This is not a group table")
            return False

    #----------------------------------------------------------------#
    # before adding an element s to S, we check that the entries
    # in the s column with rows indexed by elements of H are distinct
    # from each other and not in H
    #
    # if this fails we can quickly find a triple violating associativity
    #
    # if this always holds, then we must have that |H| doubles with
    # every addition to S, so |S| never exceeds log_2(n)
    
    def enforce_growth(self,s):
        H=self.H
        S=self.S
        op=self.op
        a=self.a_name
        b=self.b_name
        c=self.c_name
        roadmap=self.roadmap
        identity=self.identity
        inverse=self.inverse
        Growth = {}
        for x in H:
            y = op[x][s]
            
            if y in Growth:
                z = Growth[y] # z * s = x * s = y
                if not self.suppress_output:
                    st.write(f"""
                    We have a duplicate in the ${self.element[s]}$ column: ${self.element[z]}*{self.element[s]}={self.element[x]}*{self.element[s]}={self.element[y]}$.
                    At most two triples to check before we find a violation:
                    """)
                self.failed_triple_type='right inverse'
                if self.check_triple(z,s,inverse[s]):
                    self.check_triple(x,s,inverse[s])
                    return False

            Growth[y] = x
            if y in H:
                # we have x * s in H
                if not self.suppress_output:
                    st.write(f"""
                    We have ${self.element[x]}*{self.element[s]}={self.element[y]}$, which is an element of $H$.
                    A few triples to check before we find a violation:
                    """)
                xinv = inverse[x]
                if not self.check_triple(xinv,x,s):
                    self.failed_triple_type='left inverse'
                    return False

                # we have s = xinv * y
                if xinv in H:
                    self.failed_triple_type='x inverse roadmap'
                    if not self.suppress_output:
                        st.write(f"""
                        We have ${self.element[xinv]}*{self.element[y]}={self.element[s]}$, where both ${self.element[xinv]}$ and
                        ${self.element[y]}$ are in $H$.  We will take the first
                        roadmap equation ${a}*{b}={c}$ such that ${self.element[xinv]}*{c}$
                        is not an element of $H$ (this exists because ${c}={self.element[y]}$
                        works), and we will see that the
                        triple $({self.element[xinv]},{a},{b})$ fails.
                        """)
                    
                    for i in range(0,len(roadmap)):
                        z_i = roadmap[i]['z']
                        if not op[xinv][z_i] in H:
                            x_i = roadmap[i]['x']
                            y_i = roadmap[i]['y']
                            
                            if not self.suppress_output:
                                st.write(f"""
				Found roadmap equation ${self.element[x_i]}*{self.element[y_i]}={self.element[z_i]}$
                                with ${self.element[xinv]}*{self.element[z_i]}$ not in $H$.
                                """)
                            
                            self.check_triple(xinv,x_i,y_i)
                            return False
                        # should never reach this line
                    assert False, "unreachable (?) line"

                    
                else: #xinv not in H
                    if not self.suppress_output:
                        st.write(f"""
                        We have ${self.element[x]}*{self.element[xinv]}={self.element[identity]}$, where ${self.element[x]}$ is
                        in $H$ but ${self.element[xinv]}$ is not.
                        We will look for a roadmap equation
                        ${a}*{b}={c}$ such that ${self.element[x]}*{c}$
                        is not an element of $H$. 

                        There may not be such an equation, but if
                        there is, then the triple ${self.element[x]},{a},{b}$
                        must fail.
                        """)
                    
                    for i in range(0,len(roadmap)):
                        z_i = roadmap[i]['z']
                        if not op[x][z_i] in H:
                            x_i = roadmap[i]['x']
                            y_i = roadmap[i]['y']
                            
                            self.failed_triple_type='x roadmap'
                            if not self.suppress_output:
                                st.write(f"""Found roadmap equation
                                ${self.element[x_i]}*{self.element[y_i]}={self.element[z_i]}$ with ${self.element[x]}*{self.element[z_i]}$
                                not in $H$.""")

                            self.check_triple(x,x_i,y_i)
                            return False

                    if not self.suppress_output:
                        st.write(f"""
                        There is no such equation, so
                        the ${self.element[x]}$ row of the table
                        must have a repeated entry (since the ${self.element[xinv]}$
                        column as well as all the $H$ columns
                        contain elements of $H$).
                        """)
                    # x * maps H to H
                    self.failed_triple_type='xH'                        
                    xH = {identity:xinv}
                    for v in H:
                        xv = op[x][v]
                        if xv in xH:
                            u = xH[xv]
                            if not self.suppress_output:
                                st.write(f"""
                                We have ${self.element[x]}*{self.element[u]}={self.element[x]}*{self.element[v]}$ so one of the
                                two triples $({self.element[xinv]},{self.element[x]},{self.element[u]})$ and
                                $({self.element[xinv]},{self.element[x]},{self.element[v]}$ must fail.
                                """)
                            if self.check_triple(xinv,x,u):
                                self.check_triple(xinv,x,v)
                            return False
                        else:
                            xH[xv] = v
                        
                    # should never reach this line
                    assert False, "unreachable (??) line"
        return True
    
    #----------------------------------------------------------------#
    # We need to undo the table coloration sometimes
    def plain_table(self):
        for i in range(0,self.n):
            self.row_colors[i]=self.plain
            self.col_colors[i]=self.plain
            for j in range(0,self.n):
                self.cell_colors[i][j]=self.plain

    ##################################################################
    # End of subroutines                                             #
    ##################################################################
    

    ##################################################################
    # Main routines                                                  #
    ##################################################################

    #----------------------------------------------------------------#
    # Find a generating set and roadmap

    def find_roadmap(self):
        
        identity= self.identity
        element = self.element
        op      = self.op
        n       = self.n
        roadmap = self.roadmap
        Queue   = self.Queue
        H       = self.H
        S       = self.S
        untried = self.untried


        # start with H = {identity}
        if len(H)==0:
            H[identity]=True
            
            if not self.suppress_output:            
                i=identity
                self.row_colors[i]=self.H_color
                for j in range(0,n):
                    self.cell_colors[i][j]=self.H_color
                self.H_string=r"$H=\{"+f"{self.element[identity]}"+r"\}$"

                a=self.a_name
                b=self.b_name
                c=self.c_name
                st.write(f"""
                # Associativity
                ## Finding a generating set
                
                Before testing the table for associativity,
                we will compute a *generating set* $S$, that is,
                a set such that we can express every element (other
                than the identity) as a product of elements of $S$.
                
                As we compute $S$, we will keep track of the set $H$
                of elements we know how to express as products of
                elements of $S$.  We start with $H={self.element[identity]}$,
                since ${self.element[identity]}$ is the empty product.
                And any time we
                add an element to $S$, we may add it to $H$ as well.
                
                This process will be indicated by coloring the table as
                follows: rows indexed by elements of $H$ will be
                highlighted in yellow. Columns indexed by
                elements of $S$ will be highlighted in pink. Where
                these rows and column intersect, the table will initially
                by highlighted in orange.
                
                We process each orange position at most once.
                Let $({a},{b})$ be the indices of an orange position,
                so ${a}$ is in $H$ and ${b}$ is an element of $S$.
                We examine the element ${c}={a}* {b}$ in that
                orange position.
                
                
                  - Case 1: ${c}$ is not in $H$.

                     * Add ${c}$ to $H$, highlighting the ${c}$ row
                       yellow.

                     * Change the $({a},{b})$ position from orange to red.

                     * Record the equation ${c}={a}* {b}$ on our
                       *road map*.

                  - Case 2: Change the $({a},{b})$ position to grey-orange.

                Think of $H$ as being *known territory*.  The road map
                records how to get to each newly reached element of
                $H$ from previously reached elements.

                When there are no orange positions, if there are any elements
                ${a}$ not in $H$, we will pick one and try to add it to $S$.
                Before adding ${a}$ to $S$, however, we check that the
                yellow entries in the ${a}$ column are distinct from each
                other and not in $H$.  If this condition fails, we will
                quickly be able to find a triple violating associativity.
                On the other hand, if this condition always holds, then
                the set $S$ will be small.  For a set of size ${self.n}$,
                we will have $|S|$ at most ${math.floor(math.log2(self.n))}$.
        
                Once every element has been added to $H$, we will be ready to
                start testing triples.

                """)
                self.pause()

                  
        while len(H) < n:

            if not self.suppress_output:                           
                self.print_status()
                self.roadmap_step=self.roadmap_step+1
                st.write(f"""
                ## Finding a generating set, step {self.roadmap_step}
                """)

            
            # close H under right multiplication by S
            if Queue.size() > 0:
                item=Queue.pop()

                x = item['x']
                y = item['s']
                z = op[x][y]

                if not self.suppress_output:            
                
                    st.write(f"""
                    Processing orange entry in position $({self.element[x]},{self.element[y]})$.
                    
                    We find ${self.element[x]}*{self.element[y]}={self.element[z]}$...
                    
                    """)
                
                if not z in H:
                    H.add(z) # appends S,z pairs to Queue
                    roadmap.add({'x':x, 'y':y, 'z':z}) #equation x * y = z
                    if not self.test_mode:
                        self.roadmap_string=self.roadmap_string+f"   - ${self.element[x]}*{self.element[y]}={self.element[z]}$\n"
                    if not self.suppress_output:            
                        st.write(f"""
                        ... and ${self.element[z]}$ is not in $H$.  So we add ${self.element[z]}$ to $H$ and
                        add ${self.element[x]}*{self.element[y]}={self.element[z]}$ to our list of roadmap equations.
                        
                        """)
                        self.pause()
                    
                else:
                    if not self.suppress_output:            
                    
                        st.write(f"""
                        ... and ${self.element[z]}$ is already in $H$, so we do nothing here.
                        
                        """)
                        
                        self.pause()

            else:
                if not self.suppress_output:            

                    st.write("""
                    There are no plain orange positions. This means that
                    $H$ is closed under right multiplication by elements of $S$.
                    In order to make progress, we must find some element not
                    in $H$ and add it to $S$.

                    """)
                
                
                # find some s in G \ H
                s=untried.pop()
                while s in H:
                    s=untried.pop()

                if not self.suppress_output:            
                    
                    st.write(f"""
                    Trying the element ${self.element[s]}$.
                    
                    We have to check that the yellow entries in the
                    ${self.element[s]}$ column are distinct from each other and
                    not already in $H$.  If that fails, then we can quickly
                    find a triple violating associativity.
                    
                    """)

                # enforce growth condition
                if not self.enforce_growth(s):
                    return False

                if not self.suppress_output:                            
                    st.write(f"""
                    The element ${self.element[s]}$ checks out! adding it to both $H$ and $S$.
                    
                    """)
                
                # add s to both S and H
                S.add(s) # appends H,s pairs to Queue
                H.add(s) # appends s,S pairs to Queue
                
                if not self.suppress_output:            
                    self.pause()
                 
        self.found_roadmap=True
        if not self.suppress_output:                    
            self.print_status()
            st.write(f"""
            We now have $|H|={n}$, so $S$ is a generating set.
            """)
            self.plain_table()
            self.pause()
        return True
    
    def test_triples(self):

        n       = self.n
        identity= self.identity
        op      = self.op
        opT     = self.opT
        S       = self.S
        S_size  = len(S)
        roadmap = self.roadmap
        a       = self.a_name
        b       = self.b_name
        c       = self.c_name
        element = self.element

        # the triples come in batches

 
        if not hasattr(self,'batch_count'):
            self.batch_count=0
            if not self.suppress_output:                        
                st.write(f"""
                # Associativity
                ## Checking triples
                """)
                st.write(f"""
                Now that we have our generating set {self.S_string}
                together with {self.roadmap_string}
                
                """)
                st.write(f"""
                We are ready to start checking triples of elements
                $({a},{b},{c})$, testing whether
                $$
                ({a}*{b})*{c}={a}*({b}*{c}).
                $$
                If ever that fails, we are done: we can safely conclude
                that the table is not a group table.
                
                On the other hand, suppose every triple we check passes its
                test? At what point can we conclude that associativity holds
                for *all* triples? Must we actually test all ${n}^3={n*n*n}$
                triples?
                
                We will see that if we are careful, we need only test
                ${(n-S_size-1)*(n-S_size-1)+(n-1)*S_size*S_size}$ triples.  We will organize
                the triples into *batches*, each of which has a purpose
                which we will state as we go.
                
                Each batch will have two of the elements ${a},{b},{c}$
                fixed while the other varies.  We never need to check
                a triple that includes ${self.element[identity]}$ since those would
                pass automatically.  So the maximum batch size is ${n-1}$.
                
                   - A batch for which ${a}$ and ${c}$ are fixed will 
                     establish that the operation of
                     left-multiplying an element by ${a}$ *commutes*
                     with the operation of right-multiplying an element
                     by ${c}$. That is, applying those two operations,
                     in either order, to all elements ${b}$ yields the
                     same result (assuming all triples 
                     pass their tests).

                   - A batch for which ${a}$ and ${b}$ are fixed will
                     establish that the operation of left-multiplying
                     an element
                     by $({a}*{b})$ is the composition of the operation
                     of left-multiplying by ${a}$ with the operation
                     of left-multiplying by ${b}$ (assuming all triples
                     pass their tests).
          

                   - A batch for which ${b}$ and ${c}$ are fixed will
                     establish that the operation of right-multiplying
                     an element
                     by $({b}*{c})$ is the composition of the operation
                     of right-multiplying by ${c}$ with the operation
                     of right-multiplying by ${b}$ (assuming all triples
                     pass their tests).

                By organizing the triples into batches in this manner,
                we will be able to keep track of our knowledge, and
                eventually conclude with certainty that the table defines
                a group (assuming all triples pass their tests).

                We will maintain a set $X$, such that we have established
                that for any triple $({a},{b},{c})$ with both ${a},{c}$
                in $X$, $({a}*{b})*{c}={a}*({b}*{c})$.
                That is, for all ${a},{c}$ in $X$, left-multiplication
                by ${a}$ commutes with right-multiplication by ${c}$.

                As $X$ gets larger, the batches will get smaller,
                since we can omit from the batch any triples
                which start and end with elements of $X$.
                
                Once everything is in $X$,
                we will know that associativity holds.
                """)
                self.X_string=r"$X=\{"+f"{self.element[identity]}"+r"\}$"
                self.pause()
            elif not self.test_mode:
                st.write("Generating set "+self.S_string)
                st.write("R"+self.roadmap_string[1:])
                
        nonidentity   =np.array(range(n))
        nonidentity   =nonidentity[np.where(nonidentity!=identity)]

        while self.batch_count < S_size*S_size:
            i = self.batch_count // S_size
            j = self.batch_count - S_size*i
            self.batch_count=self.batch_count+1

            s=S[i]
            t=S[j]

            if self.suppress_output:
                if not self.test_mode:                
                    st.write("----")
            else:
                # s row
                self.row_colors[s]="yellow"
                for j in range(0,n):
                    self.cell_colors[s][j]="yellow"
                
                # t column
                self.col_colors[t]="yellow"
                for i in range(0,n):
                    self.cell_colors[i][t]="yellow"
                    
                self.print_status()

                # then make it plain colors again
                # s row
                self.row_colors[s]=self.plain
                for j in range(0,n):
                    self.cell_colors[s][j]=self.plain
                
                # t column
                self.col_colors[t]=self.plain
                for i in range(0,n):
                    self.cell_colors[i][t]=self.plain
                
                st.write(f"## Checking triples, batch {self.batch_count}")
                st.write(f"{self.X_string}")
                st.write(f"""
                For any ${a},{b}$ in $X$,
                left multiplication by ${a}$
                commutes with right multiplication by ${b}$.
                
                Checking whether left multiplication by ${self.element[s]}$ commutes
                with right multiplication by ${self.element[t]}$: 
                """)
                
            # check all s,g,t triples for g != identity
            if not self.test_mode:
                for g in range(self.n):
                    if not g == identity:
                        if not self.check_triple(s,g,t):
                            self.failed_triple_type='S'
                            return False

            else: # avoid function call overhead in test_mode
                g=nonidentity
                sg=op[s][g]
                gt=opT[t][g]
                sg_t=opT[t][sg]
                s_gt=op[s][gt]
                self.number_of_triples=self.number_of_triples+n-1
                if not (sg_t==s_gt).all():
                    g_bad=g[np.where(sg_t!=s_gt)][0]
                    self.failed_triple=[element[s],element[g_bad],element[t]]
                    self.failed_triple_type='S'
                    return False                    
                
            if (s==t) and (not self.suppress_output):
                self.X_string=self.X_string[:-3]+f",{self.element[s]}"+r"\}$"

            if (self.batch_count == S_size*S_size) and (len(roadmap)==0):
                if not self.test_mode:
                    st.write(f"""
                    ----
                
                    All {self.number_of_triples} required triples check out!!! This is a group table.
                    """)
                return True
            else:    
                if not self.suppress_output:
                    self.pause()

        roadmap_length=len(roadmap)
        roadmap_z     =np.array([roadmap[i]['z'] for i in range(roadmap_length)])
        
        while self.batch_count < S_size*S_size+2*roadmap_length:
            # now we check triples based on the road map
            # two batches per equation
            roadmap_index    =  self.batch_count - S_size*S_size
            parity           =  roadmap_index%2
            roadmap_index    =  (roadmap_index-parity)//2

            self.batch_count = self.batch_count + 1
            
            equation=roadmap[roadmap_index]
            x = equation['x']
            y = equation['y']
            z = equation['z']
                
            if self.suppress_output:
                if not self.test_mode:
                    st.write("----")
            else:
                if parity==0:
                    # batch is x * y * g triples
                    # so highlight x,y,z rows
                    for l in [x,y,z]:
                        self.row_colors[l]="yellow"
                        for m in range(0,n):
                            self.cell_colors[l][m]="yellow"
                        
                    self.print_status()
                
                    # make table plain again
                    for l in [x,y,z]:
                        self.row_colors[l]=self.plain
                        for m in range(0,n):
                            self.cell_colors[l][m]=self.plain
                            
                            
                else: 
                    # batch is g * x * y triples
                    # so highlight x,y,z columns                    
                    for l in [x,y,z]:
                        self.col_colors[l]="yellow"
                        for m in range(0,n):
                            self.cell_colors[m][l]="yellow"
                            
                    self.print_status()
                
                    # make table plain again
                    for l in [x,y,z]:
                        self.col_colors[l]=self.plain
                        for m in range(0,n):
                            self.cell_colors[m][l]=self.plain
                        
                st.write(f"## Checking triples, batch {self.batch_count}")
                st.write(f"{self.X_string}")
                st.write(f"""
                For any ${a},{b}$ in $X$,
                left multiplication by ${a}$
                commutes with right multiplication by ${b}$.
                """)
            
            if parity==0:
                if not self.suppress_output:                
                    st.write(f"""
                    Working with Roadmap equation
                    ${self.element[x]}*{self.element[y]}={self.element[z]}$:
                    
                    Checking whether left multiplication by
                    ${self.element[z]}$ is the composition of left
                    multiplication by ${self.element[x]}$ and left
                    multiplication by ${self.element[y]}$. If this
                    checks out, we will have established left
                    multiplication by ${self.element[z]}$ commutes
                    with right multiplication by elements of $X$.
                    
                    We have that ${self.element[x]}$ is in $X$. We
                    must check all triples
                    $({self.element[x]},{self.element[y]},{c})$ with
                    ${c}$ not in $X$, since for ${c}$ in $X$ we know
                    that left multiplication by ${self.element[x]}$
                    commutes with right multiplication by ${c}$.
                    """)

                if not self.test_mode:
                    for j in range(roadmap_index,roadmap_length):
                        z_j = roadmap[j]['z']
                        if not self.check_triple(x,y,z_j,ab=z):
                            self.failed_triple_type='roadmap left'
                            return False
                else:
                    z_j=roadmap_z[range(roadmap_index,roadmap_length)]

                    zz_j   = op[z][z_j]
                    yz_j   = op[y][z_j]
                    x_yz_j = op[x][yz_j]
                    self.number_of_triples=self.number_of_triples+roadmap_length-roadmap_index
                    if not (zz_j==x_yz_j).all():
                        z_bad=z_j[np.where(zz_j!=x_yz_j)][0]
                        self.failed_triple=[element[x],element[y],element[z_bad]]
                        self.failed_triple_type='roadmap left'
                        return False
                            

                if not self.suppress_output:                    
                    self.pause()
                
            else:
                if not self.suppress_output:        
                    st.write(f"""
                    Working with Roadmap equation ${self.element[x]}*{self.element[y]}={self.element[z]}$:
                    
                    Checking whether right multiplication by ${self.element[z]}$ is
                    the composition of right multiplication by ${self.element[y]}$ and
                    right multiplication by ${self.element[x]}$. If this checks out,
                    we will have established right multiplication by ${self.element[z]}$
                    commutes with left multiplication by elements
                    of $X$ and also with left multiplication by ${self.element[z]}$.
                    Thus, we will be able to add ${self.element[z]}$ to $X$
                    
                    We have that ${self.element[y]}$ is in $X$. We only check
                    triples $({a},{self.element[x]},{self.element[y]})$ with ${a}$ not in $X$,
                    since for ${a}$ in $X$ we know that left multiplication
                    by ${a}$ commutes with right multiplication by ${self.element[y]}$.
                    
                    But we just established (in the previous batch) that
                    left multiplication by ${self.element[z]}$ commutes with right
                    multiplication by ${self.element[y]}$: we don't need to check
                    ${a}={self.element[z]}$.
                    
                    """)
                    
                if roadmap_index+1 < roadmap_length:
                    if not self.test_mode:
                        for j in range(roadmap_index+1,roadmap_length):
                            z_j = roadmap[j]['z']
                            if not self.check_triple(z_j,x,y,bc=z):
                                self.failed_triple_type='roadmap right'
                                return False
                    else:
                        z_j=roadmap_z[range(roadmap_index+1,roadmap_length)]

                        z_jz   = opT[z][z_j]
                        z_jx   = opT[x][z_j]
                        z_jx_y = opT[y][z_jx]
                        self.number_of_triples=self.number_of_triples+roadmap_length-roadmap_index-1
                        if not (z_jz==z_jx_y).all():
                            z_bad=z_j[np.where(z_jz!=z_jx_y)][0]
                            self.failed_triple=[element[z_bad],element[x],element[y]]
                            self.failed_triple_type='roadmap right'
                            return False
                            
                    if not self.suppress_output:                    
                        self.X_string=self.X_string[:-3]+f",{self.element[z]}"+r"\}$"
                        self.pause()

                else:
                    if not self.suppress_output:                    
                        st.write(f"""
                        There are no triples to check!!!
                        We may add ${self.element[z]}$ to $X$!

                        Every element is now in $X$!!!
                        """)
                        
                    if not self.test_mode:
                        st.write(f"All {self.number_of_triples} required triples check out!!! This is a group table.")
                    return True

                
        
        # should only get here with a 1 x 1 table
        if not self.test_mode:
            st.write("This is a group table")
        return True
        
    def test_table(self):

        timings={}
        if not (self.introduced or self.test_mode):
            self.intro()


        if not hasattr(self,"closed"):
            start_time=time.process_time()                        
            if not self.test_closure():
                return {'is_group':False,
                        'failed_property':'closure',
                        'failed_product':self.failed_product
                        }
            timings['closure']=time.process_time()-start_time
            if not self.suppress_output:
                self.pause()

        if not hasattr(self,"identity"):
            start_time=time.process_time()                        
            if not self.test_identity():
                return {'is_group':False,
                        'failed_property':'identity'
                        }
            timings['identity']=time.process_time()-start_time
            if not self.suppress_output:
                self.pause()

        if not hasattr(self,"inverse"):
            start_time=time.process_time()                        
            if not self.test_inverses():
                return {'is_group':False,
                        'failed_property':'inverses',
                        'failed_inverse':self.failed_inverse
                        }
            timings['inverse']=time.process_time()-start_time
            if not self.suppress_output:
                self.pause()

        
        if (len(self.H) < self.n) or (not hasattr(self,"found_roadmap")):
            start_time=time.process_time()                        
            if not self.find_roadmap():
                return {'is_group':False,
                        'failed_property':'associativity',
                        'failed_triple':self.failed_triple,
                        'failed_triple_type':self.failed_triple_type,
                        'number_of_triples':self.number_of_triples
                        }
            timings['roadmap']=time.process_time()-start_time
            if not self.suppress_output:
                self.pause()

        start_time=time.process_time()
        if not self.test_triples():
            return {'is_group':False,
                    'failed_property':'associativity',
                    'failed_triple':self.failed_triple,
                    'failed_triple_type':self.failed_triple_type,
                    'number_of_triples':self.number_of_triples
                    }
        else:
            timings['triples']=time.process_time()-start_time
            return {'is_group':True,
                    'number_of_triples':self.number_of_triples,
                    'generators':list(self.S),
                    'identity':self.identity,
                    'inverse':self.inverse,
                    'roadmap':list(self.roadmap),
                    'timings':timings
                    }
            



def explain_method():        
        page1 = r'''
        ### Introduction

        We demonstrate a new method of testing whether a given
        $n\times n$ table for a binary operation $*$ defines a
        group. Let $G$ denote the $n$-element set of row / column
        indices.  There are four properties to check:

         - Closure: for all $a,b\in G$, we have $a*b\in G$.

         - Identity: for some element $e\in G$, for all $a\in G$,
           we have $e*a=a*e=a$.

         - Inverses: for all $a\in G$, there is an element $a^{-1}\in G$
           such that $a*a^{-1}=a^{-1}*a=e$.

         - Associativity: for all $a,b,c\in G$, we have $(a*b)*c=a*(b*c)$.

        The first three of these properties are readily checked;
        we do nothing new for these.
        But associativity is trickier, and our method for
        testing it is innovative.
        

        ### New result
        This python script is a companion to a paper [1]
        in which we give an elementary algorithm which
        tests about $n^2$ triples (that is, $n^2$ plus lower order terms).
        The goal is to make associativity somewhat less mysterious
        for students who have just been introduced to groups, and
        to satisfy the curiosity of those who wonder about the difficulty
        of checking group tables.  The problem does not arise in practice,
        except in homework exercises.
        
        ### Prior work
        Naively, one would test all $n^3$ triples.

        A method of
        F. W. Light from the 1940's (see [2,Section 1.2])
        tests at most $(n-1)^2\log_2 n$ triples.


        Rajagopalan and Schulman [3] in the 1990's developed a
        randomized algorithm running in time $O(n^2)$.  If the
        operation is not associative, then each run of their algorithm
        has at least a $1/8$ chance of detecting this.  By iterating
        the algorithm $\ell$ times, the detection probability
        increases to $1-(7/8)^\ell$.

        
        In 2024 Evra, Gadot, Klein, and Komargodski [4]
        gave the first deterministic $O(n^2)$ algorithm.
        They check, for at least $16(n^2-2n^{3/2})$ quadruples
        of elements $(a,b,c,d)$, that all five ways of parenthesizing
        $a*b*c*d$ agree.  Their algorithm 
        depends on the Classification of Finite Simple Groups.
        '''
        page2 = r'''
        ### Details of the new method

        We check the first three properties (closure, identity, and
        inverses) first.  We then find a set $S\subseteq G$ with $|S|$
        at most $\log_2 n$ such that the closure of $S$ under $*$ is
        all of $G$.  In some cases this fails, and the circumstances
        of this failure quickly lead to a triple violating associativity.

        As we find $S$, we record a *road map* of $G$, describing how to
        reach every non-identity element of $G\setminus S$ can be
        expressed as a product of previously reached elements. We
        have, for $i=1,\ldots,n-|S|-1$:
        $$
                     z_i = x_i * y_i
        $$
        where $x_i,y_i\in S\cup\{z_j\mid j<i\}$ and
        $$
                     G = \{e\}\cup S \cup \{z_1,\ldots,z_{n-|S|-1}\}.
        $$
        We test

          - The $|S|^2 (n-1)$ triples $(s,g,t)$ with $s,t\in S$
            and $g\in G\setminus\{e\}$.

          - The $(n-|S|-1)^2$ triples
            determined by the road map. For each pair $i,j$ with
            $1\leq i,j\leq n-|S|-1$, we test:
            $$
                          (x_i,y_i,z_j)
            $$
            if $i\leq j$, or 
            $$
                          (z_j,x_i,y_i) 
            $$
            if $i> j$.

        We prove that if all these triples pass, then $G$ is a group.
        '''
        page3=r'''
        ### Comparison with other methods

        Light's method, like ours, computes a generating
        set $S$.  Then all triples $(g,s,h)$ 
        with $g,h\in G\setminus\{e\}$ and $s\in S$ are tested.
        That is, $|S|(n-1)^2$, which is always more than
        the
        $$
                      (n-|S|-1)^2+|S|^2(n-1)
        $$
        triples tested by the new method.
        

        The method of Evra, Gadot, Klein, and Komargodski [4]
        finds a set $S$ such that $S*S=G$ and
        $$
          2\sqrt{n}-1\leq |S| \leq 2\sqrt{2n}
        $$
        and they check, for all $|S|^4$ quadruples
        of elements $(a,b,c,d)$ of $S$, that all
        five ways of parenthesizing
        $a*b*c*d$ agree.  This is always more quadruples than
        the number of triples tested by our method.
        The lower bound on $|S|$ comes from their
        construction: $S=A\cup B$ with $A*B=G$ and
        $A\cap B=\{e\}$.  Thus $|A||B|\geq n$, so
        $|A|+|B|\geq 2\sqrt{n}$ and $|S|\geq 2\sqrt{n}-1$.


        The method of Rajagopalan and Schulman [3]
        has an entirely different flavor.  They extend
        the operation $*$ to work with subsets of $G$,
        defining $A*B=X$ to mean that $X$ consists
        of those elements $x$ of $G$ such that
        $a*b=x$ has an odd number of solutions with $a\in A$
        and $b\in B$. Observe that for $a,b\in G$ this gives
        $\{a\}*\{b\}=\{a*b\}$.
        They show that $*$ is associative for subsets iff
        it is associative for elements, and that
        if $*$ is not
        associative, then it fails at least $1/8$ of the
        time for random subsets $A,B,C$ of $G$.  Determining whether
        $A*(B*C)=(A*B)*C$ takes time $O(n^2)$. Repeating $\ell$ times
        with random subsets $A,B,C$ will detect
        a non-associative operation with probability at least $1-(7/8)^\ell$.

        '''
        
        refs=r'''
        
        ### Bibliography
          [[1]](https://doi.org/10.1080/00029890.2025.2557077)
              R. Beals.
              Testing whether a table defines a group.
              Amer. Math. Monthly, to appear.

          [[2]](https://web.abo.fi/fak/mnf/mate/kurser/semigrupper/Light.pdf)
              A. H. Clifford, G. B. Preston.
              The algebraic theory of semigroups. Vol. I.
              Mathematical Surveys, No. 7. American Mathematical Society,
              Providence, RI; 1961.

          [[3]](https://doi.org/10.1137/S0097539797325387)
              S. Rajagopalan, L. J. Schulman.
              Verification of identities. SIAM J Comput. 2000;29(4):1155--1163.
              

          [[4]](https://doi.org/10.1109/FOCS61266.2024.00126).
              S. Evra, S. Gadot, O. Klein, I. Komargodski.
              Verifying groups in linear time.
              In: 65th Annual Symposium on Foundations of Computer
              Science (Chigago, IL), 2024. p. 2163--2179.

        '''

        if 'page1' not in st.session_state:
            st.write(page1+refs)
            st.session_state.page1=True
            done=st.button("Details",type="primary")
            st.stop()
        elif 'page2' not in st.session_state:
            st.write(page1+page2+refs)
            st.session_state.page2=True
            done=st.button("Comparison of methods",type="primary")
            st.stop()
        else:
            del[st.session_state.page1]
            del[st.session_state.page2]
            st.write(page1+page2+page3+refs)

def homework():
    # if we already hit the GO button there is
    # no need to ask for input 
    if 'elements' in st.session_state:
        elements=list(st.session_state.elements)
        table=[]
        n=len(elements)
        m=0
        ok=True
        for x in elements:
            elts_x=f"elements_{x}"
            if elts_x in st.session_state:
                new_row=list(st.session_state[elts_x])
                if(len(new_row)==n):
                    table.append(new_row)
                    m=m+1
                else:
                    ok=False
                    
        if ok and (m==n):
            table=np.array(table)
            del st.session_state['elements']
            st.session_state.G=group_table_checker(elements, table)
            st.session_state.current_task=st.session_state.G.test_table
            st.session_state.current_task()
            del st.session_state.current_task
            done=st.button("Return to main menu",type="primary")
            st.stop()
        
    st.write(r"""
    # Input your table

    First, enter the names of the elements of your set, without commas,
    ordered as in the table.  For example, if your set is
    $\{a,b,c,d,e\}$ and the $a$ row is first, and the $b$ row is second,
    etc, then enter 'abcde'.
    """)
    elements=list(st.text_input("Elements",key="elements"))
    ok=True
    index={}
    for i in range(0,len(elements)):
        a=elements[i]
        if a in index:
            ok=False
            violation=f"Element '${a}$' occurs more than once"
            st.write(f":red[{violation}]")
        else:
            index[a]=i

    if (len(elements)>0) and ok:
        with st.form("table input"):
            st.write("Enter the rows of the table.")
            st.write("When finished, press return or click the GO button.")
            table=[]
            for x in elements:
                table.append(list(st.text_input(f"Enter the {x} row of the table",key=f"elements_{x}")))
            st.write("Make sure all rows are the same length before submitting.")
            st.write("(The GO button won't work unless the row lengths are equal.)")
            submit=st.form_submit_button("GO!",type="primary")
            
        st.stop()
    st.stop()


def show_table(X,title=""):

    fig, ax = plt.subplots()
    ax.axis('off')  # Hide axes
    ax.set_aspect('equal')
    table = ax.table(cellText=X['table'],
                     cellLoc='center',
                     loc='center',
                     rowLabels=X['elts'],
                     rowLoc='center',
                     colLabels=X['elts'],
                     colLoc='center',
                     )

    if len(title) > 0:
        ax.set_title(title)
        
    #table.auto_set_font_size(False)
    #    table.set_fontsize(10)

    table._autoColumns=[]
    #set cell height and width.
    n=len(X['elts'])
    for (row, col), cell in table.get_celld().items():
        if row > 0:
            cell.set_height(2/(2*n+1))
        else:
            cell.set_height(1/(2*n+1))
        if col > -1:
            cell.set_width(2/(2*n+1))
        else:
            cell.set_width(1/(2*n+1))


    st.pyplot(fig)
    plt.close(fig)


def test_mode():
    histogram={'group':0,
               'right inverse':0,
               'left inverse':0,
               'x inverse roadmap':0,
               'x roadmap':0,
               'xH':0,
               'S':0,
               'roadmap left':0,
               'roadmap right':0}

    def random_perm(n):
        pi=np.array(range(n))
        for i in range(n-1):
            j=np.random.randint(low=i,high=n)
            tmp=pi[i]
            pi[i]=pi[j]
            pi[j]=tmp
        return(pi)

    def permute(X):
        n=len(X['elts'])
        pi=random_perm(n)
        if X['elts']==list(range(n)):
            identity=np.array(range(n))
            pi_inverse=identity.copy()
            pi_inverse[pi]=identity
            Y={
                'table':pi_inverse[X['table'][pi].T[pi].T],
                'elts':X['elts']
            }
        else:
            Y={
                'table':X['table'][pi].T[pi].T,
                'elts':[X['elts'][i] for i in pi]
            }
            
        return Y

    def tester(X,summary,update_histogram=False):
        start_time=time.process_time()
        G=group_table_checker(
            X['elts'],
            X['table'],
            test_mode=True,
        )
        results = G.test_table()
        process_time=time.process_time()-start_time
        n=len(X['elts'])
        if not update_histogram:
            summary=summary+f"{n}x{n} table, is_group={results['is_group']}, "
            if results['is_group']:
                k=len(results['generators'])
                num_triples=results['number_of_triples']
                ok=num_triples==(n-k-1)*(n-k-1)+(n-1)*k*k
                summary=summary+f" k={k}, number of triples = {num_triples}, time={process_time}"#, ok={ok}, timing={results['timings']}"
            else:  # failed_property is one of
                # ['closure','identity','inverses','associativity']
                failed=results['failed_property']
                summary=summary+f"failed:{failed}"
                if failed=='closure':
                    summary=summary+f": {results['failed_product']}"
                elif failed=='inverses':
                    summary=summary+f": {results['failed_inverse']}"
                elif failed=='associativity':
                    # failed triple is one of these types:
                    # ['right inverse', 'left inverse', 'x inverse roadmap',
                    #  'x roadmap', 'xH', 'S', 'roadmap left', 'roadmap right']
                    summary=summary+f": {results['number_of_triples']}. {results['failed_triple']} ({results['failed_triple_type']})"
                    
            st.write(summary)
        else: #update histogram on various aspects of result
              #use for tables known to have closure, identity, inverses
            if not results['is_group']:
                if results['failed_property']=='associativity':
                    rslts=f"{results['failed_triple_type']}"
                    histogram[rslts]=histogram[rslts]+1
            else:
                histogram['group']=histogram['group']+1
                    
        return process_time


    def RS_test(X):
        elements=X['elts']
        n=len(elements)
        table=X['table']

        if not elements==list(range(n)):
            raise ValueError(f"elements are not range({n})")
        
        def RS_prod(U,V):
            H=np.zeros((n),dtype=int)
            for u in U:
                H[table[u,V]]+=1
            return np.where(H%2>0)[0]

        A=np.where(np.random.randint(low=0,
                                     high=2,
                                     size=n)>0)[0]
        
        B=np.where(np.random.randint(low=0,
                                     high=2,
                                     size=n)>0)[0]
        
        C=np.where(np.random.randint(low=0,
                                     high=2,
                                     size=n)>0)[0]
        
        AB=RS_prod(A,B)
        BC=RS_prod(B,C)
        AB_C=RS_prod(AB,C)
        A_BC=RS_prod(A,BC)
        return (len(AB_C)==len(A_BC)) and (AB_C==A_BC).all()           
    
    
    # check if a closed table with elements list(range(n)) is a latin square
    def latin_square(X):
        elements=X['elts']
        n=len(elements)
        table=X['table']
        if not elements==list(range(n)):
            raise ValueError(f"elements are not range({n})")

        H=np.zeros((n,n),dtype=int)
        for i in range(n):
            H[i][table[i]]+=1
        if H.min()==0:
            return False

        tableT=table.T
        for i in range(n):
            H[i][tableT[i]]+=1
        if H.min()==1:
            return False
        return True
        
            
    # check a closed table with elements list(range(n))
    # returns False if no identity, no inverse, or
    # failed triple (x,x_inverse,a) or (a,x,x_inverse)
    # has x_inverse * (x * a) = a and
    #     (a * x) * x_inverse = a 
    def latin_square_combo(X):
        table=X['table']
        elements=X['elts']
        n=len(elements)
        if not elements==list(range(n)):
            raise ValueError(f"elements are not range({n})")
        a=0
        indices=np.where(table[0]==a)
        if not len(indices)==1:
            return False # should be unique index
        id=indices[0][0]
        if not (table[id]==elements).all():
            return False #not a left identity
        id_col=table[:,id]
        if not (id_col==elements).all():
            return False #not a right identity

        table_transpose=table.T
        
        done={}    
        for a in elements:
            if not a in done:
                indices=np.where(table[a]==id)
                if not len(indices)==1:
                    return False # should be unique index
                a_inv=indices[0][0]
                left=table[a][table[a_inv]]
                if not (left==elements).all():
                    return False
#                right=table[:,a][table[:,a_inv]]
                right=table_transpose[a_inv][table_transpose[a]]


                if not (right==elements).all():
                    return False

                done[a]=True
                done[a_inv]=True
        return True
    

    
    def perm_enum(x,n):
        rho=list(range(n))
        for i in range(n-2,-1,-1):
            j = i + x%(n-i)
            x = x // (n-i)
            tmp=rho[i]
            rho[i]=rho[j]
            rho[j]=tmp
        return rho

    def perm_index(x):
        rho=x.copy()
        n=len(rho)
        x=0
        for i in range(n):
            j=rho.index(i)
            tmp=rho[i]
            rho[i]=rho[j]
            rho[j]=tmp
            x=x*(n-i)+j-i
        return(x)

    def perm_mult(rho,sigma):
        return [rho[i] for i in sigma]

    def symmetric_group(k):
        n=math.factorial(k)
        pi=random_perm(n)
        pi_inverse=list(range(n))
        for i in range(n):
            pi_inverse[pi[i]]=i

        elements=list(range(n))
        table=np.zeros((n,n),dtype=int)

        alpha=list(range(k))
        alpha[0]=1
        alpha[1]=0

        a=pi[perm_index(alpha)] 
        for j in range(n):
            rho=perm_enum(pi_inverse[j],k)
            sigma=perm_mult(alpha,rho)
            t=perm_index(sigma)
            table[a,j]=pi[t]

        beta=list(range(1,k+1))
        beta[k-1]=0
        b=pi[perm_index(beta)]
        for j in range(n):
            rho=perm_enum(pi_inverse[j],k)
            sigma=perm_mult(beta,rho)
            t=perm_index(sigma)
            table[b,j]=pi[t]

        Q=[a,b]
        while len(Q) > 0:
            x=Q.pop()
            ax=table[a][x]
            bx=table[b][x]
            if table[ax].max() == 0:
                table[ax]=table[a][table[x]]
                Q.append(ax)
                

            if table[bx].max() == 0:
                table[bx]=table[b][table[x]]
                Q.append(bx)

        return {
            'table': table,
            'elts': elements
            }

    def elementary_two_group(k):
        n=1<<k;
        elements=list(range(n))
        x=np.array(elements)
        table=np.zeros((n,n),dtype=int)
        for i in range(n):
            table[i]=i^x
        return {
            'table': table,
            'elts': elements
            }

    # find an element x of order 2
    # swap entries in a,a*x rows intersect b,x*b column
    def table_tweak(T):
        elements=T['elts']
        table=T['table']
        n=len(elements)
        if not (n%2==0):
            raise ValueError(f"the order {n} is not even")
        if not elements==list(range(n)):
            raise ValueError(f"elements are not range({n})")
        a=0
        indices=np.where(table[0]==a)
        if not len(indices)==1:
            return False # should be unique index
        id=indices[0][0]

        x=np.random.randint(low=0,high=n)
        while (table[x][x]!=id) or (x==id):
            x=np.random.randint(low=0,high=n)

        a=np.random.randint(low=0,high=n)
        while (a==x) or (a==id):
            a=np.random.randint(low=0,high=n)
            
        b=np.random.randint(low=0,high=n)
        while (b==x) or (b==id) or (table[a][b]==id) or (table[b][a]==x):
            b=np.random.randint(low=0,high=n)
        
        ax=table[a][x]
        xb=table[x][b]
        ab=table[a][b]
        axb=table[ax][b]

        table[a][b]=axb
        table[a][xb]=ab
        table[ax][b]=ab
        table[ax][xb]=axb


    
    def random_table(n):
        elements=list(range(n))
        table=[]
        for i in range(n):
            table.append([])
            for j in range(n):
                table[i].append(np.random.randint(low=0,high=n))
        id=np.random.randint(low=0,high=n)
        for i in range(n):
            table[i][id]=i
            table[id][i]=i
        
        available={}
        for i in range(n):
            available[i]=True

        del available[id]
        while len(available)>0:
            i=np.random.choice(list(available.keys()))
            j=np.random.choice(list(available.keys()))
            table[i][j]=id
            table[j][i]=id
            del available[i]
            if not (i==j):
                del available[j]
        return {
            'table': np.array(table),
            'elts': elements
            }
                

    def basic_diagnostics():
        quaternions={
            'table': np.array([
                list("abcdefgh"),
                list("badcfehg"),
                list("cdbaghfe"),
                list("dcabhgef"),
                list("efhgbacd"),
                list("feghabdc"),
                list("ghefdcba"),
                list("hgfecdab"),
            ]),
            'elts': list("abcdefgh")
        }
        X=permute(quaternions)
        tester(X,"quaternion group: ")
        
        not_closed={
            'table': np.array([
                list("abcdefgh"),
                list("badcfehg"),
                list("cdbaghfe"),
                list("dcaBhgef"),
                list("efhgbacd"),
                list("feghabdc"),
                list("ghefdcba"),
                list("hgfecdab"),
            ]),
            'elts': list("abcdefgh")
        }
        X=permute(not_closed)
        tester(X,"non-closed operation: ")
        
        no_right_id={
            'table': np.array([
                list("abcdefgh"),
                list("badcfehg"),
                list("cdbaghfe"),
                list("ecabhgef"),
                list("dfhgbacd"),
                list("feghabdc"),
                list("ghefdcba"),
                list("hgfecdab"),
            ]),
            'elts': list("abcdefgh")
        }
        X=permute(no_right_id)
        tester(X,"no right identity:")
        
        
        
        no_left_id={
            'table': np.array([
                list("abcdfegh"),
                list("badcfehg"),
                list("cdbaghfe"),
                list("dcabhgef"),
                list("efhgbacd"),
                list("feghabdc"),
                list("ghefdcba"),
                list("hgfecdab"),
            ]),
            'elts': list("abcdefgh")
        }
        X=permute(no_left_id)
        tester(X,"no left identity: ")
        
        no_inverses={
            'table': np.array([
                list("abcdefgh"),
                list("badcfehg"),
                list("cdbaghfe"),
                list("dcabhgef"),
                list("efhgbcad"),
                list("feghcbda"),
                list("ghefdabc"),
                list("hgfeadcb"),
            ]),
            'elts': list("abcdefgh")
        }
        X=permute(no_inverses)
        tester(X,"without inverses: ")

        X=random_table(125)
        tester(X,"random: ")
        
        st.write("trying 10000 random 25x25 tables (satisfying closure, identity, and inverses)")
        
        for i in range(10000):
            X=random_table(25)
            tester(X,"random: ",update_histogram=True)
        st.write(histogram)

        st.write("trying 10000 24x24 tables (latin squares which are off from a group table in four squares")
            
        for i in range(10000):
            X=symmetric_group(4)
            table_tweak(X)
            tester(X,"latin: ",update_histogram=True)
        st.write(histogram)
        
        done=st.button("Return to diagnostics menu",type="primary")
        st.stop()

    def time_test():
        timings = []
        orders  = []
        st.write("""
        ### Timing results on large tables

        We will generate and test tables for Sym($i$) for $i\in\{4,5,6,7\}$,
        and for ${Z_2}^i$ for $4\leq i\leq 12$.
        For each of these groups we will print the table size, the result
        of the table test (should be 'True'), and the number $k$
        of generators (usually 2 for Sym($i$), always $i$ for ${Z_2}^i$).
        Note that the larger groups will take some time.
        """)

        X=elementary_two_group(4)
        timings.append(tester(X,"(Z_2)^4: "))
        orders.append(16)
        
        X=symmetric_group(4)
        timings.append(tester(X,"Sym(4): "))
        orders.append(24)
        
        X=elementary_two_group(5)
        timings.append(tester(X,"(Z_2)^5: "))
        orders.append(32)
        
        X=elementary_two_group(6)
        timings.append(tester(X,"(Z_2)^6: "))
        orders.append(64)
        
        X=symmetric_group(5)
        timings.append(tester(X,"Sym(5): "))
        orders.append(120)

        X=elementary_two_group(7)
        timings.append(tester(X,"(Z_2)^7: "))
        orders.append(128)
        
        X=elementary_two_group(8)
        timings.append(tester(X,"(Z_2)^8: "))
        orders.append(256)

        X=elementary_two_group(9)
        timings.append(tester(X,"(Z_2)^9: "))
        orders.append(512)
        
        X=symmetric_group(6)
        timings.append(tester(X,"Sym(6): "))
        orders.append(720)

        X=elementary_two_group(10)
        timings.append(tester(X,"(Z_2)^10: "))
        orders.append(1024)
        
        X=elementary_two_group(11)
        timings.append(tester(X,"(Z_2)^11: "))
        orders.append(2048)
        
        X=elementary_two_group(12)
        timings.append(tester(X,"(Z_2)^12: "))
        orders.append(4096)
        
#        start_time=time.process_time()
        X=symmetric_group(7)
#        construction_time=time.process_time()-start_time

#        start_time=time.process_time()
#        latin_test = latin_square(X)
#        latin_time=time.process_time()-start_time

#        start_time=time.process_time()
#        latin_test_combo= latin_square_combo(X)
#        latin_combo_time=time.process_time()-start_time
        timings.append(tester(X,"Sym(7): "))
        orders.append(5040)

        timings=np.array(timings)
        orders=np.array(orders)
        fig,ax = plt.subplots()
        ax.set_xlabel("Order of group")
        ax.set_ylabel("Time (sec)")
        ax.scatter(orders,timings,s=60,alpha=0.7,edgecolors="k")
        c,b,a = np.polyfit(orders,timings,deg=2)
        xseq=np.linspace(0,5040,num=100)
        ax.plot(xseq,a+b*xseq+c*xseq*xseq,color="k",lw=2.5)
        C=round(1000000*c,3)
        st.write(f"""
        ### Summary of results

        Time is approximately ${C}$ microseconds per table entry.
        """)
        st.pyplot(fig)
        plt.close(fig)
        
#        st.write(f", ")
#        st.write(f"""
#        For Sym(7): breakdown of computation time:
#          - construction of group table         : {construction_time}
#          - test if table is latin square       : {latin_time}
#          - new method test (all properties)    : {timings[trials-1]}
#        """)
        
        done=st.button("Return to main menu",type="primary")
        if 'current_task' in st.session_state:
            del st.session_state.current_task
        if 'go' in st.session_state:
            del st.session_state.go
        if 'option' in st.session_state:
            del st.session_state.option
        if 'test_option' in st.session_state:
            del st.session_state.test_option

        st.stop()
        

            
#########################################################################
#  Main test_mode routine
#########################################################################
    basic="Basic diagnostics on small tables"
    timing="Timing results on large tables"
    upload="Upload a table to test"
    main="Return to Main Menu"
    option_names=[
        basic,
        timing,
        main
    ]
    if 'test_go' in st.session_state and st.session_state.test_go:
        option=st.session_state.test_option
        del st.session_state.test_go
        if option==basic:
            basic_diagnostics()
        elif option==timing:
            time_test()
        else:
            st.session_state.current_task=main_menu
            st.session_state.current_task()
        
    else:
        option=st.radio("Please select an option, then click the GO button",
                        option_names, #index=None,
                        key="test_option")
        st.button("GO", key="test_go",type="primary")
        st.stop()
    
def demo():
    
    sym_three={
        'table': np.array([
            list("abcdef"),
            list("badcfe"),
            list("cfebad"),
            list("defabc"),
            list("edafcb"),
            list("fcbeda")]),
        'elts': list("abcdef")
        }

    not_closed={
        'table': np.array([
            list("abcdefgh"),
            list("badcfehg"),
            list("cdbaghfe"),
            list("dcaBhgef"),
            list("efhgbacd"),
            list("feghabdc"),
            list("ghefdcba"),
            list("hgfecdab"),
        ]),
        'elts': list("abcdefgh")
    }

    

    sym_three_broken={
        'table': np.array([
            list("abcdef"),
            list("badcfe"),
            list("cfebad"),
            list("defacb"),
            list("edafbc"),
            list("fcbeda")]),
        'elts': list("abcdef")
        }

    c_five={
        'elts': list("abcde"),
        'table': np.array([
            list("abcde"),
            list("bcdea"),
            list("cdeab"),
            list("deabc"),
            list("eabcd")
            ])
        }
    
    five_broken={
        'elts': list("abcde"),
        'table': np.array([
            list("abcde"),
            list("bcaed"),
            list("caebd"),
            list("debca"),
            list("edbac")
            ])
    }

    if ("table_option" in st.session_state and
        not st.session_state.table_option==None):
        option=st.session_state.table_option
        del st.session_state.table_option
        if option=="Example 1":
            X=sym_three
        elif option=="Example 2":
#            X=not_closed
            X=sym_three_broken
        elif option=="Example 3":
            X=c_five
        else:# option=="Example 4":
            X=five_broken
        
        G=group_table_checker(
            X['elts'],
            X['table']
        )

        st.session_state.current_task=G.test_table

        st.session_state.current_task()
        del st.session_state.current_task
        done=st.button("Return to main menu",type="primary")
        st.stop()

    
    
    c1,c2,c3=st.columns(3)
    with c1:
        show_table(sym_three,title="Example 1")
        show_table(c_five,title="Example 3")
    with c2:
#        show_table(not_closed,title="Example 2")
        show_table(sym_three_broken,title="Example 2")
        show_table(five_broken,title="Example 4")
    with c3:
        with st.form("Table selection"):
            
            option=st.radio("Please select a table, then click the GO button",
                            ["Example 1",
                             "Example 2",
                             "Example 3",
                             "Example 4"], index=None,
                            key="table_option")
            
            submit=st.form_submit_button("GO!",type="primary")
            st.stop()
        st.stop()
    st.stop()


def main_menu():
    WhatIsGroup="What is a group?"
    WhatIsNew="Let's hear more about this new method!"
    Homework="Let's see it in action! I have a table to test"
    Demo="Let's see it in action on a sample table"
#    TestMode="Diagnostics"
    TestMode="Timing results on large tables"


    if ('go' in st.session_state) and st.session_state.go:
        del st.session_state.go
        option=st.session_state.option
        del st.session_state.option
    
        if option==WhatIsNew:
            current_task=explain_method
        elif option==Homework:
            current_task=homework
        elif option==Demo:
            current_task=demo
        elif option==TestMode:
            current_task=test_mode
            # here we are shortcutting past the diagnostics menu
            st.session_state.test_option="Timing results on large tables"
            st.session_state.test_go=True
            
        st.session_state.current_task=current_task
        current_task()
        del st.session_state.current_task
        done=st.button("Return to main menu",type="primary")
        st.stop()
    else:

        
        option_names= [WhatIsNew,
                       Demo,
                       Homework,
                       TestMode
                       ]
        st.header("Welcome to the Group Table Checker!")
        st.subheader("Presenting a new table-testing method")

        c_three={
            'elts':  list("ABC"),
            'table': np.array([list("ABC"),
                               list("BCA"),
                               list("CAB")]),
        }
        col1,col2=st.columns(2)
        with col1:
            show_table(c_three)
        with col2:    
            st.write(r"""
            A binary operation $*$ on a set, such as $\{A,B,C\}$,
            can be defined by a table like the one on the left.
            
            To see what $B * C$ is, for example look in the
            row $B$ column $C$ entry of the table: we see $B*C=A$.
            Note that this happens to equal $C*B$, but it need not,
            since these are given by different table entries.
            
            A *group* is a set with a binary operation satisfying
            certain properties.  If we are given a table, how can
            we tell if it defines a group?
            
            We present here a new, more efficient method.
            """)
        
        with col1:
            option=st.radio("Please select an option, then click the GO button",
                            option_names, #index=None,
                            key="option")
        with col2:
            st.button("GO", key="go",type="primary")

        st.stop()
        
#st.write("---")
#st.write("# Session state")
#st.write(st.session_state)
#st.write("---")
        
if 'current_task' not in st.session_state:
    st.session_state.current_task=main_menu
    
st.session_state.current_task()
del st.session_state.current_task
done=st.button("Return to main menu",type="primary")
st.stop()
