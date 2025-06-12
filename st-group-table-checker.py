import streamlit as st
import matplotlib.pyplot as plt
import math

# shell command:
# streamlit run streamGroupTableChecker.py

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
        i=self.index[equation['x']]
        j=self.index[equation['y']]
        self.cell_colors[i][j]=self.road_color
        
    ##################################################################
    # attributes to make a FIFO queue out of a list                  #
    ##################################################################
    def Queue_pop(self):
        item=self.Queue[self.Queue.ptr]
        i=self.index[item['x']]
        j=self.index[item['s']]
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
        i=self.index[x]
        
        for s in self.S:
            self.Queue.append({'x':x,'s':s})

        if not self.suppress_output:
            self.row_colors[i]=self.H_color
            for j in range(0,self.n):
                self.cell_colors[i][j]=self.H_color
            for s in self.S:
                j=self.index[s]
                self.cell_colors[i][j]=self.Q_color
            self.H_string=self.H_string[:-3]+f",{x}"+r"\}$"
            
    #---------------------------------------------------------------#
    def S_add(self,s):
        self.S.append(s)
        for x in self.H:
            self.Queue.append({'x':x,'s':s})

        if not self.suppress_output:
            j=self.index[s]
            self.col_colors[j]=self.S_color
            for i in range(0,self.n):
                self.cell_colors[i][j]=self.S_color
            for x in self.H:
                i=self.index[x]
                self.cell_colors[i][j]=self.Q_color
        if len(self.S)>1:
            self.S_string=self.S_string[:-3]+f",{s}"+r"\}$"
        else:
            self.S_string=self.S_string[:-3]+f"{s}"+r"\}$"

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
        self.op           = {}
        self.index        = {}

        # we color the table to indicate progress
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
        if not(self.n == len(table)):
            raise ValueError(f"{self.n} elements given but table is not {self.n} by {self.n}")

        for i in range(0,self.n):
            if not (self.n == len(table[i])):
                raise ValueError(f"{self.n} elements given but table is not {self.n} by {self.n}")
        # check that the list of elements consists of distinct entries
        # making a dictionary in the process that maps from elements to
        # indices
        for a in element:
            i=len(self.index)
            if a in self.index:
                raise ValueError(f"element {a} occurs twice")
            self.index[a]=i

        # store the group table in a dictionary so
        # we mostly don't have to work with the indices
        for a in element:
            self.op[a] = {}
            for b in element:
                self.op[a][b] = self.table[self.index[a]][self.index[b]]

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
                                         
        self.untried=element.copy()  # when we need to try adding to S
        self.untried.reverse()       # we try the elements in order

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
            
        self.pause_between_pages = True
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
            col2.write("Identity element is $"+(self.identity)+"$.")
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
            
        
    #----------------------------------------------------------------#  
    # Just explain that the user should read everything before 
    # clicking
    
    def intro(self):

        standard = "Detailed explanations, one section at a time"
        all      = "Detailed explanations, all at once"
        minimal  = "Minimal output"
        if ('table_set' in st.session_state) and st.session_state.table_set:
            del st.session_state.table_set
            option=st.session_state.table_option
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
            
            table_option=st.radio("Please choose an output option",
                                  [standard,
                                   all,
                                   minimal],
                                  key="table_option")
            st.button("Proceed", key="table_set",type="primary")
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
        
        for a in self.element:
            for b in self.element:
                c = self.op[a][b]
                if not (c in self.index):
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
        while (i<self.n) and not (self.table[i] == self.element):
            i = i+1

        if(i == self.n):
            if not self.suppress_output:
                self.print_status()
                st.write(text)
                st.write(":red[There is no such row, so there is no identity].")
                st.write("This is not a group table.")
            else:
                st.write(":red[There is no identity].")
            return False

        # we have a left identity
        identity = self.element[i]
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
            We found a row that looks right! ${identity}$ is a left identity.

            We have highlighted the ${identity}$ row and the ${identity}$ column.
            Now we check whether it's also a right identity.
            """)
        

        # check if it's also a right identity
        for a in self.element:
            b = self.op[a][identity]
            if not b == a:
                if not self.suppress_output:                
                    st.write(f"It is not! We have :red[${a}*{identity}={b}$].")
                    st.write("This is not a group table.")
                else:
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
                    if(self.table[i][j]==identity):
                        self.cell_colors[i][j]="yellow"
                        
            self.print_status()

            # make table plain again
            for i in range(0,self.n):
                for j in range(0,self.n):
                    if(self.table[i][j]==identity):
                        self.cell_colors[i][j]=self.plain

        
            st.write(f"""
            # Inverses
            
            Testing whether all elements have two-sided inverses.
            
            For every element ${a_name}$, we seek an element ${b_name}$ such
            that ${a_name}*{b_name}={b_name}*{a_name}={identity}$.
            
            To make it easier to check, we have highlighted
            the identity element ${identity}$
            wherever it occurs in the table.  For there to
            be inverses, we must have a highlighted entry in every
            row and column, located symmetrically about the diagonal.
            (Technically there must be a *subset* of the
            highlighted entries with this property.)
            """)
            
        for a in self.element:
            for b in self.element:
                if (self.op[a][b] == self.identity) and (self.op[b][a] == self.identity):
                    inverse[a] = b
            if not a in inverse:
                st.write(f"""
                :red[The element ${a}$ has no inverse].
                This is not a group table.

                """)
                return False
            
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
            allgood=r"${\ \ \ \ "+f"({a}*{b})*{c}={ab}*{c}={ab_c}={a}*{bc}={a}*({b}*{c})"+r"\ \ \ \ \checkmark"+r"}$"
            st.write(f"{self.number_of_triples}. :green[{allgood}]")
            return True
        else:
            violation=r"${\ \ \ \ "+f"({a}*{b})*{c}={ab}*{c}={ab_c}"+r"\neq "+f"{a_bc}={a}*{bc}={a}*({b}*{c})"+r"}$"
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
                    We have a duplicate in the ${s}$ column: ${z}*{s}={x}*{s}={y}$.
                    At most two triples to check before we find a violation:
                    """)
                if self.check_triple(z,s,inverse[s]):
                    self.check_triple(x,s,inverse[s])
                    return False

            Growth[y] = x
            if y in H:
                # we have x * s in H
                if not self.suppress_output:
                    st.write(f"""
                    We have ${x}*{s}={y}$, which is an element of $H$.
                    A few triples to check before we find a violation:
                    """)
                xinv = inverse[x]
                if not self.check_triple(xinv,x,s):
                    return False

                # we have s = xinv * y
                if xinv in H:
                    if not self.suppress_output:
                        st.write(f"""
                        We have ${xinv}*{y}={s}$, where both ${xinv}$ and
                        ${y}$ are in $H$.  We will take the first
                        roadmap equation ${a}*{b}={c}$ such that ${xinv}*{c}$
                        is not an element of $H$ (this exists because ${c}={y}$
                        works), and we will see that the
                        triple $({xinv},{a},{b})$ fails.
                        """)
                    
                    for i in range(0,len(roadmap)):
                        z_i = roadmap[i]['z']
                        if not op[xinv][z_i] in H:
                            x_i = roadmap[i]['x']
                            y_i = roadmap[i]['y']
                            
                            if not self.suppress_output:
                                st.write(f"""
				Found roadmap equation ${x_i}*{y_i}={z_i}$
                                with ${xinv}*{z_i}$ not in $H$.
                                """)
                            
                            self.check_triple(xinv,x_i,y_i)
                            return False
                        # should never reach this line
                    assert False, "unreachable (?) line"

                    
                else: #xinv not in H
                    if not self.suppress_output:
                        st.write(f"""
                        We have ${x}*{xinv}={identity}$, where ${x}$ is
                        in $H$ but ${xinv}$ is not.
                        We will look for a roadmap equation
                        ${a}*{b}={c}$ such that ${x}*{c}$
                        is not an element of $H$. 

                        There may not be such an equation, but if
                        there is, then the triple ${x},{a},{b}$
                        must fail.
                        """)
                    
                    for i in range(0,len(roadmap)):
                        z_i = roadmap[i]['z']
                        if not op[x][z_i] in H:
                            x_i = roadmap[i]['x']
                            y_i = roadmap[i]['y']
                            
                            if not self.suppress_output:
                                st.write(f"""Found roadmap equation
                                ${x_i}*{y_i}={z_i}$ with ${x}*{z_i}$
                                not in $H$.""")

                            self.check_triple(x,x_i,y_i)
                            return False
                        
                    if not self.suppress_output:
                        st.write(f"""
                        There is no such equation, so
                        the ${x}$ row of the table
                        must have a repeated entry (since the ${xinv}$
                        column as well as all the $H$ columns
                        contain elements of $H$).
                        """)
                    # x * maps H to H
                    xH = {identity:xinv}
                    for v in H:
                        xv = op[x][v]
                        if xv in xH:
                            u = xH[xv]
                            if not self.suppress_output:
                                st.write(f"""
                                We have ${x}*{u}={x}*{v}$ so one of the
                                two triples $({xinv},{x},{u})$ and
                                $({xinv},{x},{v}$ must fail.
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
                i=self.index[identity]
                self.row_colors[i]=self.H_color
                for j in range(0,n):
                    self.cell_colors[i][j]=self.H_color
                self.H_string=r"$H=\{"+identity+r"\}$"

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
                elements of $S$.  We start with $H={identity}$, since
                ${identity}$ is the empty product. And any time we
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
                    Processing orange entry in position $({x},{y})$.
                    
                    We find ${x}*{y}={z}$...
                    
                    """)
                
                if not z in H:
                    H.add(z) # appends S,z pairs to Queue
                    roadmap.add({'x':x, 'y':y, 'z':z}) #equation x * y = z
                    self.roadmap_string=self.roadmap_string+"   - $"+x+r"*"+y+"="+z+"$\n"                    
                    if not self.suppress_output:            
                        st.write(f"""
                        ... and ${z}$ is not in $H$.  So we add ${z}$ to $H$ and
                        add ${x}*{y}={z}$ to our list of roadmap equations.
                        
                        """)
                        self.pause()
                    
                else:
                    if not self.suppress_output:            
                    
                        st.write(f"""
                        ... and ${z}$ is already in $H$, so we do nothing here.
                        
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
                    Trying the element ${s}$.
                    
                    We have to check that the yellow entries in the
                    ${s}$ column are distinct from each other and
                    not already in $H$.  If that fails, then we can quickly
                    find a triple violating associativity.
                    
                    """)

                # enforce growth condition
                if not self.enforce_growth(s):
                    return False

                if not self.suppress_output:                            
                    st.write(f"""
                    The element ${s}$ checks out! adding it to both $H$ and $S$.
                    
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
                a triple that includes ${identity}$ since those would
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
                self.X_string=r"$X=\{"+identity+r"\}$"
                self.pause()
            else:
                st.write("Generating set "+self.S_string)
                st.write("R"+self.roadmap_string[1:])
                
        while self.batch_count < S_size*S_size:
            i = self.batch_count // S_size
            j = self.batch_count - S_size*i
            self.batch_count=self.batch_count+1

            s=S[i]
            t=S[j]

            if self.suppress_output:
                st.write("----")
            else:
                # s row
                i=self.index[s]
                self.row_colors[i]="yellow"
                for j in range(0,n):
                    self.cell_colors[i][j]="yellow"
                
                # t column
                j=self.index[t]
                self.col_colors[j]="yellow"
                for i in range(0,n):
                    self.cell_colors[i][j]="yellow"
                    
                self.print_status()

                # then make it plain colors again
                # s row
                i=self.index[s]
                self.row_colors[i]=self.plain
                for j in range(0,n):
                    self.cell_colors[i][j]=self.plain
                
                # t column
                j=self.index[t]
                self.col_colors[j]=self.plain
                for i in range(0,n):
                    self.cell_colors[i][j]=self.plain
                
                st.write(f"## Checking triples, batch {self.batch_count}")
                st.write(f"{self.X_string}")
                st.write(f"""
                For any ${a},{b}$ in $X$,
                left multiplication by ${a}$
                commutes with right multiplication by ${b}$.
                
                Checking whether left multiplication by ${s}$ commutes
                with right multiplication by ${t}$: 
                """)
            
            # check all s,g,t triples for g != identity
            for g in element:
                if not g == identity:
                    if not self.check_triple(s,g,t):
                        return False
            if (s==t) and (not self.suppress_output):
                self.X_string=self.X_string[:-3]+f",{s}"+r"\}$"

            if (self.batch_count == S_size*S_size) and (len(roadmap)==0):
                st.write(f"""
                ----
                
                All {self.number_of_triples} required triples check out!!! This is a group table.
                """)
                return True
            else:    
                if not self.suppress_output:
                    self.pause()


        while self.batch_count < S_size*S_size+2*len(roadmap):
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
                
            i=self.index[x]
            j=self.index[y]
            k=self.index[z]

            if self.suppress_output:
                st.write("----")
            else:
                if parity==0:
                    # batch is x * y * g triples
                    # so highlight x,y,z rows
                    for l in [i,j,k]:
                        self.row_colors[l]="yellow"
                        for m in range(0,n):
                            self.cell_colors[l][m]="yellow"
                        
                    self.print_status()
                
                    # make table plain again
                    for l in [i,j,k]:
                        self.row_colors[l]=self.plain
                        for m in range(0,n):
                            self.cell_colors[l][m]=self.plain
                            
                            
                else: 
                    # batch is g * x * y triples
                    # so highlight x,y,z columns                    
                    for l in [i,j,k]:
                        self.col_colors[l]="yellow"
                        for m in range(0,n):
                            self.cell_colors[m][l]="yellow"
                            
                    self.print_status()
                
                    # make table plain again
                    for l in [i,j,k]:
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
                    Working with Roadmap equation ${x}*{y}={z}$:
                    
                    Checking whether left multiplication by ${z}$ is
                    the composition of left multiplication by ${x}$ and
                    left multiplication by ${y}$. If this checks out,
                    we will have established left multiplication by ${z}$
                    commutes with right multiplication by elements
                    of $X$.
                    
                    We have that ${x}$ is in $X$. We must check
                    all triples $({x},{y},{c})$ with ${c}$ not in $X$,
                    since for ${c}$ in $X$ we know that left multiplication
                    by ${x}$ commutes with right multiplication by ${c}$.
                    """)

                for j in range(roadmap_index,len(roadmap)):
                    z_j = roadmap[j]['z']
                    if not self.check_triple(x,y,z_j,ab=z):
                        return False

                if not self.suppress_output:                    
                    self.pause()
                
            else:
                if not self.suppress_output:        
                    st.write(f"""
                    Working with Roadmap equation ${x}*{y}={z}$:
                    
                    Checking whether right multiplication by ${z}$ is
                    the composition of right multiplication by ${y}$ and
                    right multiplication by ${x}$. If this checks out,
                    we will have established right multiplication by ${z}$
                    commutes with left multiplication by elements
                    of $X$ and also with left multiplication by ${z}$.
                    Thus, we will be able to add ${z}$ to $X$
                    
                    We have that ${y}$ is in $X$. We only check
                    triples $({a},{x},{y})$ with ${a}$ not in $X$,
                    since for ${a}$ in $X$ we know that left multiplication
                    by ${a}$ commutes with right multiplication by ${y}$.
                    
                    But we just established (in the previous batch) that
                    left multiplication by ${z}$ commutes with right
                    multiplication by ${y}$: we don't need to check
                    ${a}={z}$.
                    
                    """)
                    
                if roadmap_index+1 < len(roadmap):
                    for j in range(roadmap_index+1,len(roadmap)):
                        z_j = roadmap[j]['z']
                        if not self.check_triple(z_j,x,y,bc=z):
                            return False
                    if not self.suppress_output:                    
                        self.X_string=self.X_string[:-3]+f",{z}"+r"\}$"
                        self.pause()

                else:
                    if not self.suppress_output:                    
                        st.write(f"""
                        There are no triples to check!!!
                        We may add ${z}$ to $X$!

                        Every element is now in $X$!!!
                        """)
                    
                    st.write(f"All {self.number_of_triples} required triples check out!!! This is a group table.")
                    return True

                
        
        # should only get here with a 1 x 1 table
        st.write("This is a group table")
        return True
        
    def test_table(self):
        
        if not self.introduced:
            self.intro()
            
        if not hasattr(self,"closed"):
            if not self.test_closure():
                return False
            if not self.suppress_output:
                self.pause()
                
        if not hasattr(self,"identity"):
            if not self.test_identity():
                return False
            if not self.suppress_output:
                self.pause()

        if not hasattr(self,"inverse"):
            if not self.test_inverses():
                return False
            if not self.suppress_output:
                self.pause()
                
        if (len(self.H) < self.n) or (not hasattr(self,"found_roadmap")):
            if not self.find_roadmap():
                return False
            if not self.suppress_output:
                self.pause()

        return self.test_triples()



def explain_method():        
        latext = r'''
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
        This python script is a companion to a paper (currently under
        review) in which we give an elementary algorithm which
        tests about $n^2$ triples (that is, $n^2$ plus lower order terms).
        The goal is to make associativity somewhat less mysterious
        for students who have just been introduced to groups, and
        to satisfy the curiosity of those who wonder about the difficulty
        of checking group tables.  The problem does not arise in practice,
        except in homework exercises.
        
        ### Prior work
        Naively, one would test all $n^3$ triples.

        A method of
        F. W. Light from the 1940's (see [1,Section 1.2])
        tests at most $n^2\log_2 n$ triples.


        Rajagopalan and Schulman [2] in the 1990's
        developed a randomized algorithm
        taking time $O(n^2\ell)$ to achieve failure probability
        at most $(7/8)^\ell$, where the natural number $\ell$ is
        user-specified.

        In 2024 Evra, Gadot, Klein, and Komargodski [3]
        gave the first deterministic $O(n^2)$ algorithm.
        They check, for at most $81n^2$ quadruples
        of elements $(a,b,c,d)$, that all five ways of parenthesizing
        $a*b*c*d$ agree.  Their algorithm 
        depends on the Classification of Finite Simple Groups.


        ### Bibliography
          [[1]](https://web.abo.fi/fak/mnf/mate/kurser/semigrupper/Light.pdf)
              A. H. Clifford, G. B. Preston.
              The algebraic theory of semigroups. Vol. I.
              Mathematical Surveys, No. 7. American Mathematical Society,
              Providence, RI; 1961.

          [[2]](https://doi.org/10.1137/S0097539797325387)
              S. Rajagopalan, L. J. Schulman.
              Verification of identities. SIAM J Comput. 2000;29(4):1155--1163.
              

          [[3]](https://doi.org/10.1109/FOCS61266.2024.00126).
              S. Evra, S. Gadot, O. Klein, I. Komargodski.
              Verifying Groups in Linear Time.
              In: 65th Annual Symposium on Foundations of Computer
              Science (Chigago, IL), 2024. p. 2163--2179.
              
        '''
        st.write(latext)

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

    
def demo():
    
    quaternions={
        'table': [
            list("abcdefgh"),
            list("badcfehg"),
            list("cdbaghfe"),
            list("dcabhgef"),
            list("efhgbacd"),
            list("feghabdc"),
            list("ghefdcba"),
            list("hgfecdab"),
        ],
        'elts': list("abcdefgh")
    }

    sym_three={
        'table': [
            list("abcdef"),
            list("badcfe"),
            list("cfebad"),
            list("defabc"),
            list("edafcb"),
            list("fcbeda")],
        'elts': list("abcdef")
        }
    

    sym_three_broken={
        'table': [
            list("abcdef"),
            list("badcfe"),
            list("cfebad"),
            list("defacb"),
            list("edafbc"),
            list("fcbeda")],
        'elts': list("abcdef")
        }

    c_five={
        'elts': list("abcde"),
        'table': [
            list("abcde"),
            list("bcdea"),
            list("cdeab"),
            list("deabc"),
            list("eabcd")
            ]
        }
    
    five_broken={
        'elts': list("abcde"),
        'table': [
            list("abcde"),
            list("bcaed"),
            list("caebd"),
            list("debca"),
            list("edbac")
            ]
    }

    if "table_option" in st.session_state:
        option=st.session_state.table_option
        del st.session_state.option
        if option=="Example 1":
            X=sym_three
        elif option=="Example 2":
            X=sym_three_broken
        elif option=="Example 3":
            X=c_five
        else: #option=="Example 4":
            X=five_broken
        
        st.session_state.G=group_table_checker(
            X['elts'],
            X['table']
        )

        st.session_state.current_task=st.session_state.G.test_table

        st.session_state.current_task()
        del st.session_state.current_task
        done=st.button("Return to main menu",type="primary")
        st.stop()

    
    
    c1,c2,c3=st.columns(3)
    with c1:
        show_table(sym_three,title="Example 1")
        show_table(c_five,title="Example 3")
    with c2:
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

        
#st.write("---")
#st.write("# Session state")
#st.write(st.session_state)
#st.write("---")

WhatIsGroup="What is a group?"
WhatIsNew="Let's hear more about this new method!"
Homework="Let's see it in action! I have a table to test"
Demo="Let's see it in action on a sample table"


if 'current_task' in st.session_state:
    st.session_state.current_task()
    del st.session_state.current_task
    done=st.button("Return to main menu",type="primary")
    st.stop()
    
elif ('go' in st.session_state) and st.session_state.go:
    del st.session_state.go
    option=st.session_state.option
    
    if option==WhatIsNew:
        current_task=explain_method
    elif option==Homework:
        current_task=homework
    elif option==Demo:
        current_task=demo

    st.session_state.current_task=current_task
    current_task()
    del st.session_state.current_task
    done=st.button("Return to main menu",type="primary")
    st.stop()
else:    
    option_names= [WhatIsNew,
                   Demo,
                   Homework,
                   ]
    st.header("Welcome to the Group Table Checker!")
    st.subheader("Presenting a new table-testing method")

    c_three={
        'elts':  list("ABC"),
        'table': [list("ABC"),
                  list("BCA"),
                  list("CAB")],
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

        

    
